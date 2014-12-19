#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
from inspect import isclass
import __future__

from collections import Callable, Counter
import socket
from zmon_worker.functions import TimeWrapper
from graphitesend import GraphiteClient
from zmon_worker.encoder import JsonDataEncoder
from stashacc import StashAccessor
from zmon_worker.common.utils import async_memory_cache, with_retries
from zmon_worker.errors import *

import eventlog
import functools
import itertools
import json
import logging
import random
from redis_context_manager import RedisConnHandler
import time
import re
import requests
import sys
import setproctitle
from datetime import timedelta, datetime

from zmon_worker.functions import HistoryWrapper, HttpWrapper, NagiosWrapper, RedisWrapper, SnmpWrapper, JmxWrapper, TcpWrapper, \
    ping, SqlWrapper, CounterWrapper, EventLogWrapper, LdapWrapper, ExaplusWrapper, ZomcatWrapper, \
    ExceptionsWrapper, JobsWrapper, SqlOracleWrapper, JoblocksWrapper, ZmonWrapper, MySqlWrapper, \
    WhoisWrapper, MsSqlWrapper

from bisect import bisect_left
from zmon_worker.functions.time_ import parse_timedelta

from zmon_worker.notifications.mail import Mail
from zmon_worker.notifications.sms import Sms
from zmon_worker.notifications.notification import BaseNotification

from operator import itemgetter
from timeperiod import in_period, InvalidFormat

import functional
from zmon_worker.common import mathfun

logger = logging.getLogger(__name__)


# interval in seconds for sending metrics to graphite
METRICS_INTERVAL = 15
CAPTURES_INTERVAL = 10
STASH_CACHE_EXPIRATION_TIME = 3600

DEFAULT_CHECK_RESULTS_HISTORY_LENGTH = 20

TRIAL_RUN_RESULT_EXPIRY_TIME = 300

# we allow specifying condition expressions without using the "value" variable
# the following pattern is used to check if "value" has to be prepended to the condition
SIMPLE_CONDITION_PATTERN = re.compile(r'^[<>!=\[]|i[ns] ')
GRAPHITE_REPLACE_KEYCHARS = re.compile(r'[./\s]')

# round to microseconds
ROUND_SECONDS_DIGITS = 6
JMX_CONFIG_FILE = 'jmxremote.password'
KAIROS_ID_FORBIDDEN_RE = re.compile(r'[^a-zA-Z0-9\-_\.]')


EVENTS = {
    'ALERT_STARTED': eventlog.Event(0x34001, ['checkId', 'alertId', 'value']),
    'ALERT_ENDED': eventlog.Event(0x34002, ['checkId', 'alertId', 'value']),
    'ALERT_ENTITY_STARTED': eventlog.Event(0x34003, ['checkId', 'alertId', 'value', 'entity']),
    'ALERT_ENTITY_ENDED': eventlog.Event(0x34004, ['checkId', 'alertId', 'value', 'entity']),
    'DOWNTIME_STARTED': eventlog.Event(0x34005, [
        'alertId',
        'entity',
        'startTime',
        'endTime',
        'userName',
        'comment',
    ]),
    'DOWNTIME_ENDED': eventlog.Event(0x34006, [
        'alertId',
        'entity',
        'startTime',
        'endTime',
        'userName',
        'comment',
    ]),
    'SMS_SENT': eventlog.Event(0x34007, ['alertId', 'entity', 'phoneNumber', 'httpStatus']),
    'ACCESS_DENIED': eventlog.Event(0x34008, ['userName', 'entity']),
}

eventlog.register_all(EVENTS)

Sms.register_eventlog_events(EVENTS)

get_value = itemgetter('value')


class ProtectedPartial(object):

    '''
    Provides functools.partial functionality with one additional feature: if keyword arguments contain '__protected'
    key with list of arguments as value, the appropriate values will not be overwritten when calling the partial. This
    way we can prevent user from overwriting internal zmon parameters in check command. The protected key uses double
    underscore to prevent overwriting it, we reject all commands containing double underscores.
    '''

    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__partial_args = args
        self.__partial_kwargs = kwargs
        self.__protected = frozenset(kwargs.get('__protected', []))
        self.__partial_kwargs.pop('__protected', None)

    def __call__(self, *args, **kwargs):
        new_kwargs = self.__partial_kwargs.copy()
        new_kwargs.update((k, v) for (k, v) in kwargs.iteritems() if k not in self.__protected)
        return self.__func(*self.__partial_args + args, **new_kwargs)



def propartial(func, *args, **kwargs):
    '''
    >>> propartial(int, base=2)('100')
    4
    >>> propartial(int, base=2)('100', base=16)
    256
    >>> propartial(int, base=2, __protected=['base'])('100', base=16)
    4
    '''

    return ProtectedPartial(func, *args, **kwargs)


normalize_kairos_id = propartial(KAIROS_ID_FORBIDDEN_RE.sub, '_')

orig_process_title = None


def setp(check_id, entity, msg):
    global orig_process_title
    if orig_process_title == None:
        try:
            orig_process_title = setproctitle.getproctitle().split(' ')[2].split(':')[0].split('.')[0]
        except:
            orig_process_title = 'p34XX'

    setproctitle.setproctitle('zmon-worker.{} check {} on {} {} {}'.format(orig_process_title, check_id, entity, msg,
                              datetime.now().strftime('%H:%M:%S.%f')))


def get_kairosdb_value(env, name, points, tags):
    tags['env'] = env
    return {'name': name, 'datapoints': points, 'tags': tags}


def flatten(structure, key='', path='', flattened=None):
    path = str(path)
    key = str(key)

    if flattened is None:
        flattened = {}
    if type(structure) not in (dict, list):
        flattened[((path + '.' if path else '')) + key] = structure
    elif isinstance(structure, list):
        pass
    else:
        for new_key, value in structure.items():
            flatten(value, new_key, '.'.join(filter(None, [path, key])), flattened)
    return flattened

def timed(f):
    '''Decorator to "time" a function execution. Wraps the function's result in a new dict.
    >>> timed(lambda: 1)()['value']
    1
    '''

    def wrapper(*args, **kwargs):
        start = time.time()
        res = f(*args, **kwargs)
        delta = time.time() - start
        # round and use short keys as we will serialize the whole stuff as JSON
        return {'value': res, 'ts': round(start, ROUND_SECONDS_DIGITS), 'td': round(delta, ROUND_SECONDS_DIGITS)}

    return wrapper


def _get_entity_url(entity):
    '''
    >>> _get_entity_url({})

    >>> _get_entity_url({'url': 'fesn01:39820'})
    'http://fesn01:39820'

    >>> _get_entity_url({'host': 'fesn01'})
    'http://fesn01'
    '''

    if 'url' in entity:
        return 'http://' + entity['url']
    if 'host' in entity:
        return 'http://' + entity['host']
    return None


def _get_jmx_port(entity):
    '''
    >>> _get_jmx_port({'instance': '9620'})
    49620
    '''

    if 'instance' in entity:
        return int('4' + entity['instance'])
    return None


def _get_shards(entity):
    '''
    >>> _get_shards({'shards': {'shard1': 'host1/db1'}})
    {'shard1': 'host1/db1'}

    >>> _get_shards({'service_name': 'db'})
    {'db': 'db/postgres'}

    >>> _get_shards({'service_name': 'db', 'port': 1234})
    {'db': 'db:1234/postgres'}

    >>> _get_shards({'service_name': 'db:1234', 'port': 1234})
    {'db:1234': 'db:1234/postgres'}

    >>> _get_shards({'service_name': 'db:1234'})
    {'db:1234': 'db:1234/postgres'}

    >>> _get_shards({'service_name': 'db-1234', 'port': 1234})
    {'db-1234': 'db-1234:1234/postgres'}

    >>> _get_shards({'project': 'shop'})
    '''

    if 'shards' in entity:
        return entity['shards']
    if 'service_name' in entity:
        return {entity['service_name']: ('{service_name}:{port}/postgres'.format(**entity) if 'port' in entity
                and not entity['service_name'].endswith(':{}'.format(entity['port'
                ])) else '{}/postgres'.format(entity['service_name']))}
    return None


def entity_values(con, check_id, alert_id):
    return map(get_value, entity_results(con, check_id, alert_id))


def entity_results(con, check_id, alert_id):
    all_entities = con.hkeys('zmon:alerts:{}:entities'.format(alert_id))
    all_results = []
    for entity_id in all_entities:
        results = get_results(con, check_id, entity_id, 1)
        all_results.extend(results)
    return all_results


def capture(value=None, captures=None, **kwargs):
    '''
    >>> capture(1, {})
    1

    >>> captures={}; capture(1, captures); captures
    1
    {'capture_1': 1}

    >>> captures={'capture_1': 1}; capture(2, captures); sorted(captures.items())
    2
    [('capture_1', 1), ('capture_2', 2)]

    >>> captures={}; capture(captures=captures, mykey=1); captures
    1
    {'mykey': 1}

    >>> p = functools.partial(capture, captures={}); p(1); p(a=1)
    1
    1
    '''

    if kwargs:
        if len(kwargs) > 1:
            raise ValueError('Only one named capture supported')
        key, value = kwargs.items()[0]
    else:
        i = 1
        while True:
            key = 'capture_{}'.format(i)
            if key not in captures:
                break
            i += 1
    captures[key] = value
    return value


def _parse_alert_parameter_value(data):
    '''
    >>> _parse_alert_parameter_value({'value': 10})
    10
    >>> _parse_alert_parameter_value({'value': '2014-07-03T22:00:00.000Z', 'comment': "desc", "type": "date"})
    datetime.date(2014, 7, 3)

    '''

    allowed_types = {
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'datetime': lambda json_date: datetime.strptime(json_date, '%Y-%m-%dT%H:%M:%S.%fZ'),
        'date': lambda json_date: datetime.strptime(json_date, '%Y-%m-%dT%H:%M:%S.%fZ').date(),
    }
    value = data['value']
    type_name = data.get('type')
    if type_name:
        try:
            value = allowed_types[type_name](value)
        except Exception:
            raise Exception('Attempted wrong type cast <{}> in alert parameters'.format(type_name))
    return value


def _inject_alert_parameters(alert_parameters, ctx):
    '''
    Inject alert parameters into the execution context dict (ctx)
    '''

    params_name = 'params'
    params = {}

    if alert_parameters:
        for apname, apdata in alert_parameters.items():
            if apname in ctx:
                raise Exception('Parameter name: %s clashes in context', apname)
            value = _parse_alert_parameter_value(apdata)
            params[apname] = value
            ctx[apname] = value  # inject parameter into context

        # inject the whole parameters map so that user can iterate over them in the alert condition
        if params_name not in ctx:
            ctx[params_name] = params


def build_condition_context(con, check_id, alert_id, entity, captures, alert_parameters):
    '''
    >>> 'timeseries_median' in build_condition_context(None, 1, 1, {'id': 1}, {}, {})
    True
    >>> 'timeseries_percentile' in build_condition_context(None, 1, 1, {'id': 1}, {}, {})
    True
    '''

    ctx = build_default_context()
    ctx['capture'] = functools.partial(capture, captures=captures)
    ctx['entity_results'] = functools.partial(entity_results, con=con, check_id=check_id, alert_id=alert_id)
    ctx['entity_values'] = functools.partial(entity_values, con=con, check_id=check_id, alert_id=alert_id)
    ctx['entity'] = dict(entity)
    ctx['history'] = functools.partial(HistoryWrapper, logger=logger, check_id=check_id, entities=entity['id'])

    _inject_alert_parameters(alert_parameters, ctx)

    for f in (
        mathfun.avg,
        mathfun.delta,
        mathfun.median,
        mathfun.percentile,
        mathfun.first,
        mathfun._min,
        mathfun._max,
        sum,
    ):
        name = f.__name__
        if name.startswith('_'):
            name = name[1:]
        ctx['timeseries_' + name] = functools.partial(_apply_aggregate_function_for_time, con=con, func=f, check_id=check_id,
                                            entity_id=entity['id'], captures=captures)
    return ctx


def _time_slice(time_spec, results):
    '''
    >>> _time_slice('1s', [])
    []

    >>> _time_slice('1s', [{'ts': 0, 'value': 0}, {'ts': 1, 'value': 10}])
    [{'ts': 0, 'value': 0}, {'ts': 1, 'value': 10}]

    >>> _time_slice('2s', [{'ts': 123.6, 'value': 10}, {'ts': 123, 'value': 0}, {'ts': 121, 'value': -10}])
    [{'ts': 123, 'value': 0}, {'ts': 123.6, 'value': 10}]
    '''

    if len(results) < 2:
        # not enough values to calculate anything
        return results
    get_ts = itemgetter('ts')
    results.sort(key=get_ts)
    keys = map(get_ts, results)
    td = parse_timedelta(time_spec)
    last = results[-1]
    needle = last['ts'] - td.total_seconds()
    idx = bisect_left(keys, needle)
    if idx == len(results):
        # timerange exceeds range of results
        return results
    return results[idx:]


def _get_results_for_time(con, check_id, entity_id, time_spec):
    results = get_results(con, check_id, entity_id, DEFAULT_CHECK_RESULTS_HISTORY_LENGTH)
    return _time_slice(time_spec, results)


def _apply_aggregate_function_for_time(
    time_spec,
    con,
    func,
    check_id,
    entity_id,
    captures,
    key=functional.id,
    **args
):

    results = _get_results_for_time(con, check_id, entity_id, time_spec)
    ret = mathfun.apply_aggregate_function(results, func, key=functional.compose(key, get_value), **args)
    # put function result in our capture dict for debugging
    # e.g. captures["delta(5m)"] = 13.5
    captures['{}({})'.format(func.__name__, time_spec)] = ret
    return ret


def _build_notify_context(alert):
    return {'send_mail': functools.partial(Mail.send, alert), 'send_sms': functools.partial(Sms.send, alert)}


def _prepare_condition(condition):
    '''function to prepend "value" to condition if necessary

    >>> _prepare_condition('>0')
    'value >0'

    >>> _prepare_condition('["a"]>0')
    'value ["a"]>0'

    >>> _prepare_condition('in (1, 2, 3)')
    'value in (1, 2, 3)'

    >>> _prepare_condition('value>0')
    'value>0'

    >>> _prepare_condition('a in (1, 2, 3)')
    'a in (1, 2, 3)'
    '''

    if SIMPLE_CONDITION_PATTERN.match(condition):
        # short condition format, e.g. ">=3"
        return 'value {}'.format(condition)
    else:
        # condition is more complex, e.g. "value > 3 and value < 10"
        return condition



def _log_event(event_name, alert, result, entity=None):
    params = {'checkId': alert['check_id'], 'alertId': alert['id'], 'value': result['value']}

    if entity:
        params['entity'] = entity

    eventlog.log(EVENTS[event_name].id, **params)


def _convert_captures(worker_name, alert_id, entity_id, timestamp, captures):
    '''
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c0': 'error'})
    []
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c1': '23.4'})
    [('p0_h.alerts.1.e1.captures.c1', 23.4, 1)]
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c2': 12})
    [('p0_h.alerts.1.e1.captures.c2', 12.0, 1)]
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c3': {'c31': '42'}})
    [('p0_h.alerts.1.e1.captures.c3.c31', 42.0, 1)]
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c4': {'c41': 'error'}})
    []
    >>> _convert_captures('p0.h', 1, 'e .1/2', 1, {'c 1/2': '23.4'})
    [('p0_h.alerts.1.e__1_2.captures.c_1_2', 23.4, 1)]
    >>> _convert_captures('p0.h', 1, 'e1', 1, {'c3': {'c 3.1/': '42'}})
    [('p0_h.alerts.1.e1.captures.c3.c_3_1_', 42.0, 1)]
    '''

    result = []
    key = '{worker_name}.alerts.{alert_id}.{entity_id}.captures.{capture}'

    safe_worker_name = GRAPHITE_REPLACE_KEYCHARS.sub('_', worker_name)
    safe_entity_id = GRAPHITE_REPLACE_KEYCHARS.sub('_', entity_id)

    for capture, value in captures.iteritems():
        safe_capture = GRAPHITE_REPLACE_KEYCHARS.sub('_', capture)
        if isinstance(value, dict):
            for inner_capture, inner_value in value.iteritems():
                try:
                    v = float(inner_value)
                except (ValueError, TypeError):
                    continue
                safe_inner_capture = GRAPHITE_REPLACE_KEYCHARS.sub('_', inner_capture)
                result.append(('{}.{}'.format(key.format(worker_name=safe_worker_name, alert_id=alert_id,
                              entity_id=safe_entity_id, capture=safe_capture), safe_inner_capture), v, timestamp))
        else:
            try:
                v = float(value)
            except (ValueError, TypeError):
                continue
            result.append((key.format(worker_name=safe_worker_name, alert_id=alert_id, entity_id=safe_entity_id,
                          capture=safe_capture), v, timestamp))

    return result



def evaluate_condition(val, condition, **ctx):
    '''

    >>> evaluate_condition(0, '>0')
    False

    >>> evaluate_condition(1, '>0')
    True

    >>> evaluate_condition(1, 'delta("5m")<-10', delta=lambda x:1)
    False

    >>> evaluate_condition({'a': 1}, '["a"]>10')
    False
    '''

    return safe_eval(_prepare_condition(condition), eval_source='<alert-condition>', value=val, **ctx)


class InvalidEvalExpression(Exception):
    pass


class MalformedCheckResult(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)


class Try(Callable):

    def __init__(self, try_call, except_call, exc_cls=Exception):
        self.try_call = try_call
        self.except_call = except_call
        self.exc_cls = exc_cls

    def __call__(self, *args):
        try:
            return self.try_call()
        except self.exc_cls, e:
            return self.except_call(e)


def get_results(con, check_id, entity_id, count):
    return map(json.loads, con.lrange('zmon:checks:{}:{}'.format(check_id, entity_id), 0, count - 1))


def avg(sequence):
    '''
    >>> avg([])
    0
    >>> avg([1, 2, 3])
    2.0
    >>> avg([2, 3])
    2.5
    '''

    l = len(sequence) * 1.0
    return (sum(sequence) / l if l else 0)


def empty(v):
    '''
    >>> empty([])
    True
    >>> empty([1])
    False
    '''

    return not bool(v)


def build_default_context():
    return {
        'abs': abs,
        'all': all,
        'any': any,
        'avg': avg,
        'basestring': basestring,
        'bin': bin,
        'bool': bool,
        'chain': itertools.chain,
        'chr': chr,
        'Counter': Counter,
        'dict': dict,
        'divmod': divmod,
        'Exception': Exception,
        'empty': empty,
        'enumerate': enumerate,
        'False': False,
        'filter': filter,
        'float': float,
        'groupby': itertools.groupby,
        'hex': hex,
        'int': int,
        'isinstance': isinstance,
        'json': json.loads,
        'len': len,
        'list': list,
        'long': long,
        'map': map,
        'max': max,
        'min': min,
        'normalvariate': random.normalvariate,
        'oct': oct,
        'ord': ord,
        'pow': pow,
        'range': range,
        'reduce': functools.reduce,
        'reversed': reversed,
        'round': round,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'time': TimeWrapper,
        'True': True,
        'Try': Try,
        'tuple': tuple,
        'unichr': unichr,
        'unicode': unicode,
        'xrange': xrange,
        'zip': zip,
    }


def check_ast_node_is_safe(node):
    '''
    Check that the ast node does not contain any system attribute calls
    as well as exec call (not to construct the system attribute names with strings).

    eval() function calls should not be a problem, as it is hopefuly not exposed
    in the globals and __builtins__

    >>> node = ast.parse('def __call__(): return 1')
    >>> node == check_ast_node_is_safe(node)
    True

    >>> check_ast_node_is_safe(ast.parse('def m(): return ().__class__'))
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition should not try to access hidden attributes (for example '__class__')


    >>> check_ast_node_is_safe(ast.parse('def horror(g): exec "exploit = ().__" + "class" + "__" in g'))
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition should not try to execute arbitrary code

    '''

    for n in ast.walk(node):
        if isinstance(n, ast.Attribute):
            if n.attr.startswith('__'):
                raise InvalidEvalExpression("alert definition should not try to access hidden attributes (for example '__class__')"
                                            )
        elif isinstance(n, ast.Exec):
            raise InvalidEvalExpression('alert definition should not try to execute arbitrary code')
    return node


def safe_eval(expr, eval_source='<string>', **kwargs):
    '''
    Safely execute expr.

    For now expr can be only one python expression, a function definition
    or a callable class definition.

    If the expression is returning a callable object (like lambda function
    or Try() object) it will be called and a result of the call will be returned.

    If a result of calling of the defined function or class are returning a callable object
    it will not be called.

    As access to the hidden attributes is protected by check_ast_node_is_safe() method
    we should not have any problem with valnarabilites defined here:
    Link: http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html

    TODO: implement compile object cache

    >>> safe_eval('value > 0', value=1)
    True

    >>> safe_eval('def m(): return value', value=10)
    10

    >>> safe_eval('def m(param): return value', value=10)
    Traceback (most recent call last):
        ...
    TypeError: m() takes exactly 1 argument (0 given)

    >>> safe_eval('lambda: value', value=10)
    10

    >>> result = safe_eval('def m(): print value', value=10)
    Traceback (most recent call last):
        ...
    SyntaxError: invalid syntax

    >>> result = safe_eval('print value', value=10)
    Traceback (most recent call last):
        ...
    SyntaxError: invalid syntax

    >>> safe_eval('def m(): return lambda: value', value=10) #doctest: +ELLIPSIS
    <function <lambda> at ...>

    >>> safe_eval('error = value', value=10)
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition can contain a python expression, a function call or a callable class definition

    >>> safe_eval('def m(): return value.__class__', value=10)
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition should not try to access hidden attributes (for example '__class__')

    >>> safe_eval("""
    ... class CallableClass(object):
    ...
    ...     def get_value(self):
    ...         return value
    ...
    ...     def __call__(self):
    ...         return self.get_value()
    ... """, value=10)
    10

    >>> safe_eval("""
    ... class NotCallableClass(object):
    ...
    ...     def get_value(self):
    ...         return value
    ...
    ...     def call(self): # this is not a callable class
    ...         return self.get_value()
    ... """, value=10)
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition should contain a callable class definition (missing __call__ method?)


    >>> safe_eval("""
    ... def firstfunc():
    ...     return value
    ...
    ... value > 0
    ...
    ... """, value=10)
    Traceback (most recent call last):
        ...
    InvalidEvalExpression: alert definition should contain only one python expression, a function call or a callable class definition

    '''

    g = {'__builtins__': {}, 'object': object, '__name__': __name__}
    # __builtins__ should be masked away to disable builtin functions
    # object is needed if the NewStyle class is being created
    # __name__ is needed to be able to complie a class
    g.update(kwargs)

    node = compile(expr, eval_source, 'exec', ast.PyCF_ONLY_AST | __future__.CO_FUTURE_PRINT_FUNCTION)
    node = check_ast_node_is_safe(node)
    body = node.body
    if body and len(body) == 1:
        x = body[0]
        if isinstance(x, ast.FunctionDef) or isinstance(x, ast.ClassDef):
            cc = compile(node, eval_source, 'exec')  # can be nicely cached
            v = {}
            exec (cc, g, v)
            if len(v) == 1:
                c = v.itervalues().next()
                if isclass(c):
                    # we need a class instance and not the class itself
                    c = c()

                if callable(c):
                    return c()  # if a function will return another callable, we will not call it
                else:
                    raise InvalidEvalExpression('alert definition should contain a callable class definition (missing __call__ method?)'
                                                )
            else:
                raise InvalidEvalExpression('alert definition should contain only one function or one callable class definition'
                                            )
        elif isinstance(x, ast.Expr):
            cc = compile(expr, eval_source, 'eval', __future__.CO_FUTURE_PRINT_FUNCTION)  # can be nicely cached
            r = eval(cc, g)
            if callable(r):
                # Try() returns callable that should be executed
                return r()
            else:
                return r
        else:
            raise InvalidEvalExpression('alert definition can contain a python expression, a function call or a callable class definition'
                                        )
    else:
        raise InvalidEvalExpression('alert definition should contain only one python expression, a function call or a callable class definition'
                                    )

class NotaZmonTask(object):

    abstract = True
    _host = 'localhost'
    _port = 6379
    _secure_queue = 'zmon:queue:secure'
    _db = 0
    _con = None
    _graphite = None
    _counter = Counter()
    _captures_local = []
    _last_metrics_sent = 0
    _last_captures_sent = 0
    _logger = None
    _logfile = None
    _loglevel = logging.DEBUG
    _pg_user = None
    _pg_pass = None
    _my_user = None
    _my_pass = None
    _loungemysql_user = None
    _loungemysql_pass = None
    _ora_user = None
    _ora_pass = None
    _mssql_user = None
    _mssql_pass = None
    _kairosdb_enabled = False
    _kairosdb_host = None
    _kairosdb_port = None
    _kairosdb_env = None
    _ldappass = None
    _ldapuser = None
    _hetcrawler_proxy_user = None
    _hetcrawler_proxy_pass = None
    _exacrm_user = None
    _exacrm_pass = None
    _exarpc_user = None
    _exarpc_pass = None
    _exacrm_cluster = None
    _cmdb_url = None
    _zmon_url = None
    _worker_name = None
    _queues = None
    _stash = None
    _stash_cmds = None
    _safe_repositories = []

    _cassandra_enabled = False
    _cassandra_keyspace = ''
    _cassandra_time_series_enabled = False
    _cassandra_seed_nodes = []

    @classmethod
    def configure(cls, config):
        try:
            #configure RedisConnHandler
            RedisConnHandler.configure(**config)
        except KeyError:
            logger.exception('Error creating connection: ')
            raise
        #cls._loglevel = (logging.getLevelName(config['loglevel']) if 'loglevel' in config else logging.INFO)
        cls._logfile = config.get('logfile')
        cls._graphite_host = config.get('graphite.host')
        cls._graphite_port = config.get('graphite.port', 2003)
        cls._graphite_prefix = config.get('graphite.prefix', 'zmon2')
        cls._pg_user = config.get('postgres.user')
        cls._pg_pass = config.get('postgres.password')
        cls._my_user = config.get('mysql.user')
        cls._my_pass = config.get('mysql.password')
        cls._loungemysql_user = config.get('loungemysql.user')
        cls._loungemysql_pass = config.get('loungemysql.password')
        cls._ora_user = config.get('oracle.user')
        cls._ora_pass = config.get('oracle.password')
        cls._mssql_user = config.get('mssql.user')
        cls._mssql_pass = config.get('mssql.password')
        cls._soap_config = {k: v for k, v in config.items() if k.startswith('soap.service')}
        cls._kairosdb_enabled = config.get('kairosdb.enabled')
        cls._kairosdb_host = config.get('kairosdb.host')
        cls._kairosdb_port = config.get('kairosdb.port')
        cls._kairosdb_env = config.get('kairosdb.env')
        cls._ldapuser = config.get('ldap.user')
        cls._ldappass = config.get('ldap.password')
        cls._hetcrawler_proxy_user = config.get('hetcrawler.proxy_user')
        cls._hetcrawler_proxy_pass = config.get('hetcrawler.proxy_pass')
        cls._exacrm_user = config.get('exacrm.user')
        cls._exacrm_pass = config.get('exacrm.password')
        cls._exarpc_user = config.get('exasol.rpc.user')
        cls._exarpc_pass = config.get('exasol.rpc.pass')
        cls._exacrm_cluster = config.get('exacrm.cluster')
        cls._cmdb_url = config.get('cmdb.url')
        cls._zmon_url = config.get('zmon.url')
        cls._queues = config.get('zmon.queues', {}).get('local')
        cls._safe_repositories = sorted(config.get('safe_repositories', []))

        cls._logger = cls.get_configured_logger()
        cls.perload_stash_commands()

        cls._cassandra_keyspace = config.get('cassandra.keyspace')
        cls._cassandra_enabled = config.get('cassandra.enabled')
        cls._cassandra_time_series_enabled = config.get('cassandra.time_series_enabled')
        cls._cassandra_seed_nodes = config.get('cassandra.seeds')

    def __init__(self):
        self.task_context = None
        self._cmds_first_accessed = False

    @classmethod
    def is_secure_worker(cls):
        return cls._secure_queue in (cls._queues or '')

    @classmethod
    def perload_stash_commands(cls):
        cls._stash = StashAccessor(cls.get_configured_logger())
        if cls.is_secure_worker():
            try:
                cls._stash_cmds = cls._stash.get_stash_commands(*cls._safe_repositories)
                cls._logger.info('Loaded %d commands from stash secure repos', len(cls._stash_cmds))
            except Exception:
                cls._logger.exception('Error loading stash commands: ')

    @async_memory_cache.cache_on_arguments(namespace='zmon-worker', expiration_time=STASH_CACHE_EXPIRATION_TIME)
    @with_retries(max_retries=3, delay=10)
    def load_stash_commands(self, repositories):
        if not self._cmds_first_accessed:
            # ugly but needed to stop celery from refreshing the cache when task process is forked
            self._cmds_first_accessed = True
            return self._stash_cmds
        else:
            return self._stash.get_stash_commands(*repositories)

    @classmethod
    def get_configured_logger(cls):
        if not cls._logger:
            cls._logger = logger
            #cls._logger.setLevel(cls._loglevel)
            # cls._logger.propagate = False
            #
            # if cls._logfile:
            #     log_file_handler = logging.handlers.TimedRotatingFileHandler(cls._logfile, when='midnight')
            #     log_file_handler.setLevel(cls._loglevel)
            #     log_file_handler.setFormatter(logging.Formatter('%(asctime)s %(processName)s %(message)s'))
            #     cls._logger.addHandler(log_file_handler)
            #
            # exception_log_file = os.path.join(get_log_path(), 'log_database_{}_{}.log'.format(manifest.host,
            #                                   manifest.instance))
            # exception_handler = logging.handlers.TimedRotatingFileHandler(exception_log_file, when='S', interval=10)
            # exception_handler.setLevel(logging.ERROR)
            # exception_handler.setFormatter(ExceptionFormatter(EXCEPTION_LOG_FORMAT))
            # exception_handler.addFilter(ExceptionFilter(host=manifest.host, instance=manifest.instance))
            #cls._logger.addHandler(exception_handler)
        return cls._logger

    @property
    def con(self):
        if self._cassandra_enabled:
            raise NotImplementedError()
        else:
            self.logger.info("running with redis write only")
            #self._con = redis.StrictRedis(self._host, self._port)
            self._con = RedisConnHandler.get_instance().get_conn()

        BaseNotification.set_redis_con(self._con)

        return self._con

    @property
    def graphite(self):
        if self._graphite is None:
            self._graphite = GraphiteClient(graphite_server=self._graphite_host, graphite_port=self._graphite_port,
                                            prefix=self._graphite_prefix)
        return self._graphite

    @property
    def logger(self):
        return self.get_configured_logger()

    @property
    def worker_name(self):
        if not self._worker_name:
            self._worker_name = 'p{}.{}'.format('local', socket.gethostname())
        return self._worker_name

    def get_redis_host(self):
        return RedisConnHandler.get_instance().get_parsed_redis().hostname

    def get_redis_port(self):
        return RedisConnHandler.get_instance().get_parsed_redis().port

    def send_metrics(self):
        now = time.time()
        if now > self._last_metrics_sent + METRICS_INTERVAL:
            p = self.con.pipeline()
            p.sadd('zmon:metrics', self.worker_name)
            for key, val in self._counter.items():
                p.incrby('zmon:metrics:{}:{}'.format(self.worker_name, key), val)
            # reset counter
            self._counter.clear()
            p.set('zmon:metrics:{}:ts'.format(self.worker_name), now)
            p.execute()
            self._last_metrics_sent = now
            self.logger.info('Send metrics, end storing metrics in redis count: %s, duration: %.3fs', len(self._counter), time.time() - now)

    def send_captures(self):
        '''
        Push elements from self._captures_local into redis list 'zmon:captures2graphite'
        The list elements look like: (key , value, timestamp)
        where key format is '{instance}_{host}.alerts.{alert_id}.captures.{capture_name}'
        '''

        now = time.time()
        if now > self._last_captures_sent + CAPTURES_INTERVAL:
            captures_local = self._captures_local[:]
            if captures_local:
                captures_json = [json.dumps(c, cls=JsonDataEncoder) for c in captures_local]
                self.con.rpush('zmon:captures2graphite', *captures_json)
                self._last_captures_sent = now
                # clean local list
                del self._captures_local[:len(captures_local)]


    def check_and_notify(self, req, alerts, task_context=None):
        self.task_context = task_context
        start_time = time.time()
        soft_time_limit = req['interval']
        check_id = req['check_id']
        entity_id = req['entity']['id']

        try:
            val = self.check(req)
        #TODO: need to support soft and hard time limits soon
        # except SoftTimeLimitExceeded, e:
        #     self.logger.info('Check request with id %s on entity %s exceeded soft time limit', check_id,
        #                                  entity_id)
        #     # PF-3685 It might happen that this exception was raised after sending a command to redis, but before receiving
        #     # a response. In this case, the connection object is "dirty" and when the same connection gets taken out of the
        #     # pool and reused, it'll throw an exception in redis client.
        #     self.con.connection_pool.disconnect()
        #     notify(check_and_notify, {'ts': start_time, 'td': soft_time_limit, 'value': str(e)}, req, alerts,
        #            force_alert=True)
        except CheckError, e:
            self.logger.warn('Check error for request with id %s on entity %s. Output: %s', check_id,
                                         entity_id, str(e))
            self.notify({'ts': start_time, 'td': time.time() - start_time, 'value': str(e), 'worker': self.worker_name, 'exc': 1}, req, alerts,
                   force_alert=True)
        except SecurityError, e:
            self.logger.exception('Security error in request with id %s on entity %s', check_id, entity_id)
            self.notify({'ts': start_time, 'td': time.time() - start_time, 'value': str(e), 'worker': self.worker_name, 'exc': 1}, req, alerts,
                   force_alert=True)
        except Exception, e:
            self.logger.exception('Check request with id %s on entity %s threw an exception', check_id,
                                              entity_id)
            # PF-3685 Disconnect on unknown exceptions: we don't know what actually happened, it might be that redis
            # connection is dirty. CheckError exception is "safe", it's thrown by the worker whenever the check returns a
            # different response than expected, the user doesn't have access to the checked entity or there's an error in
            # check's parameters.
            self.con.connection_pool.disconnect()
            self.notify({'ts': start_time, 'td': time.time() - start_time, 'value': str(e), 'worker': self.worker_name, 'exc': 1}, req, alerts,
                   force_alert=True)
        else:
            self.notify(val, req, alerts)

    def trial_run(self, req, alerts, task_context=None):
        self.task_context = task_context
        start_time = time.time()
        soft_time_limit = req['interval']
        entity_id = req['entity']['id']

        try:
            val = self.check_for_trial_run(req)
        #TODO: need to support soft and hard time limits soon
        # except SoftTimeLimitExceeded, e:
        #     trial_run.logger.info('Trial run on entity %s exceeded soft time limit', entity_id)
        #     trial_run.con.connection_pool.disconnect()
        #     notify_for_trial_run(trial_run, {'ts': start_time, 'td': soft_time_limit, 'value': str(e)}, req, alerts,
        #                          force_alert=True)
        except InsufficientPermissionsError, e:
            self.logger.info('Access denied for user %s to run check on %s', req['created_by'], entity_id)
            eventlog.log(EVENTS['ACCESS_DENIED'].id, userName=req['created_by'], entity=entity_id)
            self.notify_for_trial_run({'ts': start_time, 'td': time.time() - start_time, 'value': str(e)}, req,
                                 alerts, force_alert=True)
        except CheckError, e:
            self.logger.warn('Trial run on entity %s failed. Output: %s', entity_id, str(e))
            self.notify_for_trial_run({'ts': start_time, 'td': time.time() - start_time, 'value': str(e)}, req,
                                 alerts, force_alert=True)
        except Exception, e:
            self.logger.exception('Trial run on entity %s threw an exception', entity_id)
            self.con.connection_pool.disconnect()
            self.notify_for_trial_run({'ts': start_time, 'td': time.time() - start_time, 'value': str(e)}, req,
                                 alerts, force_alert=True)
        else:
            self.notify_for_trial_run(val, req, alerts)


    def cleanup(self, *args, **kwargs):
        self.task_context = kwargs.get('task_context')
        p = self.con.pipeline()
        p.smembers('zmon:checks')
        p.smembers('zmon:alerts')
        check_ids, alert_ids = p.execute()

        for check_id in kwargs.get('disabled_checks', {}):
            self._cleanup_check(p, check_id)

        for alert_id in kwargs.get('disabled_alerts', {}):
            self._cleanup_alert(p, alert_id)

        for check_id in check_ids:
            if check_id in kwargs.get('check_entities', {}):
                redis_entities = self.con.smembers('zmon:checks:{}'.format(check_id))
                check_entities = set(kwargs['check_entities'][check_id])

                # If it happens that we remove all entities for given check, we should remove all the things.
                if not check_entities:
                    p.srem('zmon:checks', check_id)
                    p.delete('zmon:checks:{}'.format(check_id))
                    for entity in redis_entities:
                        p.delete('zmon:checks:{}:{}'.format(check_id, entity))
                else:
                    self._cleanup_common(p, 'checks', check_id, redis_entities - check_entities)
            else:

                self._cleanup_check(p, check_id)

        for alert_id in alert_ids:
            if alert_id in kwargs.get('alert_entities', {}):
                # Entities that are in the alert state.
                redis_entities = self.con.smembers('zmon:alerts:{}'.format(alert_id))
                alert_entities = set(kwargs['alert_entities'][alert_id])

                # If it happens that we remove all entities for given alert, we should remove all the things.
                if not alert_entities:
                    p.srem('zmon:alerts', alert_id)
                    p.delete('zmon:alerts:{}'.format(alert_id))
                    p.delete('zmon:alerts:{}:entities'.format(alert_id))
                    for entity in redis_entities:
                        p.delete('zmon:alerts:{}:{}'.format(alert_id, entity))
                        p.delete('zmon:notifications:{}:{}'.format(alert_id, entity))
                else:
                    self._cleanup_common(p, 'alerts', alert_id, redis_entities - alert_entities)
                    # All entities matching given alert definition.
                    all_entities = set(self.con.hkeys('zmon:alerts:{}:entities'.format(alert_id)))
                    for entity in all_entities - alert_entities:
                        self.logger.info('Removing entity %s from hash %s', entity,
                                            'zmon:alerts:{}:entities'.format(alert_id))
                        p.hdel('zmon:alerts:{}:entities'.format(alert_id), entity)
                        p.delete('zmon:notifications:{}:{}'.format(alert_id, entity))
            else:
                self._cleanup_alert(p, alert_id)

        p.execute()


    def _cleanup_check(self, pipeline, check_id):
        self.logger.info('Removing check with id %s from zmon:checks set', check_id)
        pipeline.srem('zmon:checks', check_id)
        for entity_id in self.con.smembers('zmon:checks:{}'.format(check_id)):
            self.logger.info('Removing key %s', 'zmon:checks:{}:{}'.format(check_id, entity_id))
            pipeline.delete('zmon:checks:{}:{}'.format(check_id, entity_id))
        self.logger.info('Removing key %s', 'zmon:checks:{}'.format(check_id))
        pipeline.delete('zmon:checks:{}'.format(check_id))


    def _cleanup_alert(self, pipeline, alert_id):
        self.logger.info('Removing alert with id %s from zmon:alerts set', alert_id)
        pipeline.srem('zmon:alerts', alert_id)
        for entity_id in self.con.smembers('zmon:alerts:{}'.format(alert_id)):
            self.logger.info('Removing key %s', 'zmon:alerts:{}:{}'.format(alert_id, entity_id))
            pipeline.delete('zmon:alerts:{}:{}'.format(alert_id, entity_id))
            pipeline.delete('zmon:notifications:{}:{}'.format(alert_id, entity_id))
        self.logger.info('Removing key %s', 'zmon:alerts:{}'.format(alert_id))
        pipeline.delete('zmon:alerts:{}'.format(alert_id))
        self.logger.info('Removing key %s', 'zmon:alert:{}:entities'.format(alert_id))
        pipeline.delete('zmon:alerts:{}:entities'.format(alert_id))


    def _cleanup_common(self, pipeline, entry_type, entry_id, entities):
        '''
        Removes entities from redis matching given type and id.
        Parameters
        ----------
        entry_type: str
            Type of entry to remove: 'checks' or 'alerts'.
        entry_id: int
            Id of entry to remove.
        entities: set
            A set of entities to remove (difference between entities from scheduler and ones present in redis).
        '''

        for entity in entities:
            self.logger.info('Removing entity %s from set %s', entity, 'zmon:{}:{}'.format(entry_type, entry_id))
            pipeline.srem('zmon:{}:{}'.format(entry_type, entry_id), entity)
            self.logger.info('Removing key %s', 'zmon:{}:{}:{}'.format(entry_type, entry_id, entity))
            pipeline.delete('zmon:{}:{}:{}'.format(entry_type, entry_id, entity))

    def _store_check_result(self, req, result):
        self.con.sadd('zmon:checks', req['check_id'])
        self.con.sadd('zmon:checks:{}'.format(req['check_id']), req['entity']['id'])
        key = 'zmon:checks:{}:{}'.format(req['check_id'], req['entity']['id'])
        value = json.dumps(result, cls=JsonDataEncoder)
        self.con.lpush(key, value)
        self.con.ltrim(key, 0, DEFAULT_CHECK_RESULTS_HISTORY_LENGTH - 1)

        if self._cassandra_time_series_enabled and self._cassandra_enabled:
            self.con.getCassandraConnection().writeToHistory(key, datetime.now(), value, ttl=60*30)


    def check(self, req):

        self.logger.debug(req)
        schedule_time = req['schedule_time']
        start = time.time()

        try:
            setp(req['check_id'], req['entity']['id'], 'start')
            res = self._get_check_result(req)
            setp(req['check_id'], req['entity']['id'], 'done')
        except Exception, e:
            # PF-3778 Always store check results and re-raise exception which will be handled in 'check_and_notify'.
            self._store_check_result(req, {'td': round(time.time() - start, ROUND_SECONDS_DIGITS), 'ts': round(start,
                                ROUND_SECONDS_DIGITS), 'value': str(e), 'worker': self.worker_name, 'exc': 1})
            raise
        finally:
            # Store duration in milliseconds as redis only supports integers for counters.
            self._counter.update({
                'check.count': 1,
                'check.{}.count'.format(req['check_id']): 1,
                'check.{}.duration'.format(req['check_id']): int(round(1000.0 * (time.time() - start))),
                'check.{}.latency'.format(req['check_id']): int(round(1000.0 * (start - schedule_time))),
            })
            self.send_metrics()

        setp(req['check_id'], req['entity']['id'], 'store')
        self._store_check_result(req, res)
        setp(req['check_id'], req['entity']['id'], 'store kairos')
        self._store_check_result_to_kairosdb(req, res)
        setp(req['check_id'], req['entity']['id'], 'stored')

        return res




    def check_for_trial_run(self, req):
        # fake check ID as it is used by check context
        req['check_id'] = 'trial_run'
        return self._get_check_result(req)


    @timed
    def _get_check_result_internal(self, req):

        self._enforce_security(req)
        cmd = req['command']

        ctx = self._build_check_context(req)
        try:
            result = safe_eval(cmd, eval_source='<check-command>', **ctx)
            return result() if isinstance(result, Callable) else result

        except (SyntaxError, InvalidEvalExpression), e:
            raise CheckError(str(e))

    def _get_check_result(self, req):
        r = self._get_check_result_internal(req)
        r['worker'] = self.worker_name
        return r

    def _enforce_security(self, req):
        '''
        PF-3792: Security checks for PPD
        Check tasks from the secure queue to asert the command to run is specified in stash check definition
        Side effect: modifies req to address unique PPD concerns, e.g: pp-ccsn01 needs to become ccsn01.pp in PCI env
        Raises SecurityError on check failure
        '''

        #if self.request.delivery_info.get('routing_key') == 'secure' and self.is_secure_worker():
        if self.task_context['delivery_info'].get('routing_key') == 'secure' and self.is_secure_worker():
            try:
                stash_commands = self.load_stash_commands(self._safe_repositories)
            except Exception, e:
                traceback = sys.exc_info()[2]
                raise SecurityError('Unexpected Internal error: {}'.format(e)), None, traceback

            if req['command'] not in stash_commands:
                raise SecurityError('Security violation: Non-authorized command received in ppd environment')

            # transformations of entities: hostname "pp-whatever" needs to become "whatever.pp"
            prefix = 'pp-'
            if 'host' in req['entity'] and str(req['entity']['host']).startswith(prefix):

                self.logger.warn('secure req[entity] before pp- transformations: %s', req['entity'])

                real_host = req['entity']['host']
                #secure_host = '{}.pp'.format(req['entity']['host'][3:])
                secure_host = '{}.{}'.format(req['entity']['host'][len(prefix):], prefix[:-1])
                # relplace all real host values occurrences with secure_host
                req['entity'].update({k: v.replace(real_host, secure_host) for k, v in req['entity'].items() if
                                      isinstance(v, basestring) and real_host in v and k != 'id'})

                self.logger.warn('secure req[entity] after pp- transformations: %s', req['entity'])



    def _build_check_context(self, req):
        '''Build context for check command with all necessary functions'''

        entity = req['entity']
        entity_url = _get_entity_url(entity)
        host = entity.get('host')
        port = entity.get('port')
        instance = entity.get('instance')
        external_ip = entity.get('external_ip')
        load_balancer_status = entity.get('load_balancer_status')
        data_center_code = entity.get('data_center_code')
        ora_sid = entity.get('sid')
        database = entity.get('database')
        jmx_port = _get_jmx_port(entity)
        shards = _get_shards(entity)
        ctx = build_default_context()
        soft_time_limit = req['interval']
        counter = propartial(CounterWrapper, key_prefix='{}:{}:'.format(req['check_id'], entity['id']),
                          redis_host=self.get_redis_host(), redis_port=self.get_redis_port())
        jmx = propartial(JmxWrapper, host=host, port=jmx_port)
        http = propartial(HttpWrapper, base_url=entity_url)

        ctx.update({
            'entity': entity,
            'http': http,
            'redis': propartial(RedisWrapper, host=host, counter=counter),
            'nagios': propartial(NagiosWrapper, host, logger=self.logger, exasol_user=NotaZmonTask._exarpc_user,
                              exasol_password=NotaZmonTask._exarpc_pass, lounge_mysql_user=NotaZmonTask._loungemysql_user,
                              lounge_mysql_password=NotaZmonTask._loungemysql_pass,
                              hetcrawler_proxy_user=NotaZmonTask._hetcrawler_proxy_user,
                              hetcrawler_proxy_pass=NotaZmonTask._hetcrawler_proxy_pass,
                             ),
            'snmp': propartial(SnmpWrapper, host=host),
            'jmx': jmx,
            'zomcat': propartial(ZomcatWrapper, host=host, instance=entity.get('instance'), http=http, jmx=jmx,
                              counter=counter),
            'tcp': propartial(TcpWrapper, host=host),
            'ping': propartial(ping, host=host),
            'sql': propartial(
                SqlWrapper,
                shards=shards,
                user=NotaZmonTask._pg_user,
                password=NotaZmonTask._pg_pass,
                timeout=soft_time_limit * 1000,
                check_id=req['check_id'],
                created_by=req.get('created_by'),
                __protected=['created_by', 'check_id'],
            ),
            'orasql': propartial(SqlOracleWrapper, host, port, ora_sid, user=NotaZmonTask._ora_user, password=NotaZmonTask._ora_pass),
            'mysql': propartial(MySqlWrapper, shards=shards, user=NotaZmonTask._my_user, password=NotaZmonTask._my_pass,
                             timeout=soft_time_limit * 1000),
            'mssql': propartial(MsSqlWrapper, host, port, database, user=NotaZmonTask._mssql_user, password=NotaZmonTask._mssql_pass,
                                timeout=soft_time_limit),
            'counter': counter,
            'eventlog': EventLogWrapper,
            'ldap': propartial(LdapWrapper, user=NotaZmonTask._ldapuser, password=NotaZmonTask._ldappass, host=host, counter=counter),
            'exacrm': propartial(ExaplusWrapper, cluster=NotaZmonTask._exacrm_cluster, password=NotaZmonTask._exacrm_pass,
                              user=NotaZmonTask._exacrm_user),
            'exceptions': propartial(ExceptionsWrapper, host=host, instance=entity.get('instance'), project=(entity['name'
                                  ] if entity['type'] == 'project' else None)),
            'jobs': propartial(JobsWrapper, project=entity.get('name')),
            'job_locks': propartial(JoblocksWrapper, cmdb_url=NotaZmonTask._cmdb_url, project=entity.get('name')),
            'history': propartial(HistoryWrapper, logger=logger, check_id=req['check_id'], entities=normalize_kairos_id(entity['id'])),
            'zmon': propartial(ZmonWrapper, NotaZmonTask._zmon_url, self.get_redis_host(), self.get_redis_port()),
            'whois': propartial(WhoisWrapper, host=host),
        })

        return ctx


    def _store_check_result_to_kairosdb(self, req, result):

        if not self._kairosdb_enabled:
            return

        # use tags in kairosdb to reflect top level keys in result
        # zmon.check.<checkid> as key for time series

        series_name = 'zmon.check.{}'.format(req['check_id'])
        entity = req['entity']['id']

        values = []

        if isinstance(result['value'], dict):
            flat_result = flatten(result['value'])

            for k, v in flat_result.iteritems():

                try:
                    v = float(v)
                except (ValueError, TypeError):
                    continue

                points = [[int(result['ts'] * 1000), v]]
                tags = {'entity': normalize_kairos_id(entity), 'key': normalize_kairos_id(str(k))}
                values.append(get_kairosdb_value(self._kairosdb_env, series_name, points, tags))
        else:
            try:
                v = float(result['value'])
            except (ValueError, TypeError):
                pass
            else:
                points = [[int(result['ts'] * 1000), v]]
                tags = {'entity': normalize_kairos_id(entity)}
                values.append(get_kairosdb_value(self._kairosdb_env, series_name, points, tags))

        if len(values) > 0:
            self.logger.debug(values)
            try:
                r = requests.post('http://{}:{}/api/v1/datapoints'.format(self._kairosdb_host, self._kairosdb_port),
                                  json.dumps(values), timeout=5)
                if not r.status_code in [200, 204]:
                    self.logger.error(r.text)
                    self.logger.error(json.dumps(values))
            except Exception, e:
                self.logger.error("KairosDB write failed {}".format(e))


    def evaluate_alert(self, alert_def, req, result):
        '''Check if the result triggers an alert

        The function will save the global alert state to the following redis keys:

        * zmon:alerts:<ALERT-DEF-ID>:entities    hash of entity IDs -> captures
        * zmon:alerts                            set of active alert definition IDs
        * zmon:alerts:<ALERT-DEF-ID>             set of entity IDs in alert
        * zmon:alerts:<ALERT-DEF-ID>:<ENTITY-ID> JSON with alert evaluation result for given alert definition and entity
        '''

        # captures is our map of "debug" information, e.g. to see values calculated in our condition
        captures = {}

        alert_id = alert_def['id']
        check_id = alert_def['check_id']
        alert_parameters = alert_def.get('parameters')

        try:
            result = evaluate_condition(result['value'], alert_def['condition'], **build_condition_context(self.con,
                                        check_id, alert_id, req['entity'], captures, alert_parameters))
        except Exception, e:
            captures['exception'] = str(e)
            result = True

        try:
            is_alert = bool((result() if isinstance(result, Callable) else result))
        except Exception, e:
            captures['exception'] = str(e)
            is_alert = True

        # add parameters to captures so they can be substituted in alert title
        if alert_parameters:
            pure_captures = captures.copy()
            try:
                captures = {k: p['value'] for k, p in alert_parameters.items()}
            except Exception, e:
                self.logger.exception('Error when capturing parameters: ')
            captures.update(pure_captures)

        return is_alert, captures


    def send_notification(self, notification, context):
        ctx = _build_notify_context(context)
        try:
            repeat = safe_eval(notification, eval_source='<check-command>' , **ctx)
        except Exception, e:
            # TODO Define what should happen if sending emails or sms fails.
            self.logger.exception(e)
        else:
            if repeat:
                self.con.hset('zmon:notifications:{}:{}'.format(context['alert_def']['id'], context['entity']['id']),
                              notification, time.time() + repeat)

    def notify(self, val, req, alerts, force_alert=False):
        '''
        Process check result and evaluate all alerts. Returns list of active alert IDs
        Parameters
        ----------
        val: dict
            Check result, see check function
        req: dict
            Check request dict
        alerts: list
            A list of alert definitions matching the checked entity
        force_alert: bool
            An optional flag whether to skip alert evalution and force "in alert" state. Used when check request exceeds
            time limit or throws other exception, this way unexpected conditions are always treated as alerts.
        Returns
        -------
        list
            A list of alert definitions matching given entity.
        '''

        result = []
        entity_id = req['entity']['id']
        start = time.time()

        try:
            setp(req['check_id'], entity_id, 'notify loop')
            for alert in alerts:
                alert_id = alert['id']
                alert_entities_key = 'zmon:alerts:{}'.format(alert_id)
                alerts_key = 'zmon:alerts:{}:{}'.format(alert_id, entity_id)
                notifications_key = 'zmon:notifications:{}:{}'.format(alert_id, entity_id)
                is_alert, captures = ((True, {}) if force_alert else self.evaluate_alert(alert, req, val))

                func = getattr(self.con, ('sadd' if is_alert else 'srem'))
                changed = bool(func(alert_entities_key, entity_id))

                if is_alert:
                    # bubble up: also update global set of alerts
                    alert_changed = func('zmon:alerts', alert_id)

                    if alert_changed:
                        _log_event('ALERT_STARTED', alert, val)
                else:
                    entities_in_alert = self.con.smembers(alert_entities_key)
                    if not entities_in_alert:
                        # no entity has alert => remove from global set
                        alert_changed = func('zmon:alerts', alert_id)
                        if alert_changed:
                            _log_event('ALERT_ENDED', alert, val)

                # PF-3318 If an alert has malformed time period, we should evaluate it anyway and continue with
                # the remaining alert definitions.
                try:
                    is_in_period = in_period(alert.get('period', ''))
                except InvalidFormat, e:
                    self.logger.warn('Alert with id %s has malformed time period.', alert_id)
                    captures['exception'] = '; \n'.join(filter(None, [captures.get('exception'), str(e)]))
                    is_in_period = True

                if changed and is_in_period and is_alert:
                    # notify on entity-level
                    _log_event(('ALERT_ENTITY_STARTED'), alert, val, entity_id)
                elif changed and not is_alert:
                    _log_event(('ALERT_ENTITY_ENDED'), alert, val, entity_id)


                # Always store captures for given alert-entity pair, this is also used a list of all entities matching
                # given alert id. Captures are stored here because this way we can easily link them with check results
                # (see PF-3146).
                self.con.hset('zmon:alerts:{}:entities'.format(alert_id), entity_id, json.dumps(captures,
                              cls=JsonDataEncoder))

                self._store_captures_locally(alert_id, entity_id, int(start), captures)

                if is_in_period:

                    self._counter.update({'alerts.{}.count'.format(alert_id): 1,
                                         'alerts.{}.evaluation_duration'.format(alert_id): int(round(1000.0 * (time.time()
                                         - start)))})

                    # Always evaluate downtimes, so that we don't miss downtime_ended event in case the downtime ends when
                    # the alert is no longer active.
                    downtimes = self._evaluate_downtimes(alert_id, entity_id)

                    # Store or remove the check value that triggered the alert
                    if is_alert:
                        result.append(alert_id)

                        if changed:
                            start_time = time.time()
                        else:
                            # NOTE I'm not sure if it's possible to have two workers evaluating the same alert for the same
                            # entity. If it happens, the difference in start time should negligible.
                            try:
                                start_time = json.loads(self.con.get(alerts_key))['start_time']
                            except (ValueError, TypeError):
                                self.logger.warn('Error parsing JSON alert result for key: %s', alerts_key)
                                start_time = time.time()

                        self.con.set(alerts_key, json.dumps(dict(captures=captures, downtimes=downtimes,
                                     start_time=start_time, **val), cls=JsonDataEncoder))
                    else:
                        self.con.delete(alerts_key)
                        self.con.delete(notifications_key)

                    start = time.time()
                    notification_context = {
                        'alert_def': alert,
                        'entity': req['entity'],
                        'value': val,
                        'captures': captures,
                        'worker': self.worker_name,
                        'is_alert': is_alert,
                        'changed': changed,
                        'duration': timedelta(seconds=(time.time() - start_time if is_alert and not changed else 0)),
                    }

                    #do not send notifications for downtimed alerts
                    if not downtimes:
                        if changed:
                           for notification in alert['notifications']:
                                self.send_notification(notification, notification_context)
                        else:
                            previous_times = self.con.hgetall(notifications_key)
                            for notification in alert['notifications']:
                                if notification in previous_times and time.time() > float(previous_times[notification]):
                                    self.send_notification(notification, notification_context)

                    self._counter.update({'alerts.{}.notification_duration'.format(alert_id): int(round(1000.0
                                         * (time.time() - start)))})
                    setp(req['check_id'], entity_id, 'notify loop - send metrics')
                    self.send_metrics()
                    setp(req['check_id'], entity_id, 'notify loop - send captures')
                    self.send_captures()
                    setp(req['check_id'], entity_id, 'notify loop end')
                else:
                    self.logger.debug('Alert %s is not in time period: %s', alert_id, alert['period'])
                    if is_alert:
                        entities_in_alert = self.con.smembers('zmon:alerts:{}'.format(alert_id))

                        p = self.con.pipeline()
                        p.srem('zmon:alerts:{}'.format(alert_id), entity_id)
                        p.delete('zmon:alerts:{}:{}'.format(alert_id, entity_id))
                        p.delete(notifications_key)
                        if len(entities_in_alert) == 1:
                            p.srem('zmon:alerts', alert_id)
                        p.execute()

                        self.logger.info('Removed alert with id %s on entity %s from active alerts due to time period: %s',
                                         alert_id, entity_id, alert.get('period', ''))
            setp(req['check_id'], entity_id, 'return notified')
            return result
        #TODO: except SoftTimeLimitExceeded:
        except Exception:
            # Notifications should not exceed the time limit.
            self.logger.exception('Notification for check %s reached soft time limit', req['check_name'])
            self.con.connection_pool.disconnect()
            return None






    def notify_for_trial_run(self, val, req, alerts, force_alert=False):
        """Like notify(), but for trial runs!"""

        try:
            # There must be exactly one alert in alerts.
            alert,  = alerts
            redis_key = 'zmon:trial_run:{uuid}:results'.format(uuid=(alert['id'])[3:])

            is_alert, captures = ((True, {}) if force_alert else self.evaluate_alert(alert, req, val))

            try:
                is_in_period = in_period(alert.get('period', ''))
            except InvalidFormat, e:
                self.logger.warn('Alert with id %s has malformed time period.', alert['id'])
                captures['exception'] = '; \n'.join(filter(None, [captures.get('exception'), str(e)]))
                is_in_period = True

            try:
                result_json = json.dumps({
                    'entity': req['entity'],
                    'value': val,
                    'captures': captures,
                    'is_alert': is_alert,
                    'in_period': is_in_period,
                }, cls=JsonDataEncoder)
            except TypeError, e:
                result_json = json.dumps({
                    'entity': req['entity'],
                    'value': str(e),
                    'captures': {},
                    'is_alert': is_alert,
                    'in_period': is_in_period,
                }, cls=JsonDataEncoder)

            self.con.hset(redis_key, req['entity']['id'], result_json)
            self.con.expire(redis_key, TRIAL_RUN_RESULT_EXPIRY_TIME)
            return ([alert['id']] if is_alert and is_in_period else [])

        #TODO: except SoftTimeLimitExceeded:
        except Exception:
            self.con.connection_pool.disconnect()
            return None


    def _store_captures_locally(self, alert_id, entity_id, timestamp, captures):
        metrics = _convert_captures(self.worker_name, alert_id, entity_id, timestamp, captures)
        if metrics:
            self._captures_local.extend(metrics)



    def _evaluate_downtimes(self, alert_id, entity_id):
        result = []

        p = self.con.pipeline()
        p.smembers('zmon:downtimes:{}'.format(alert_id))
        p.hgetall('zmon:downtimes:{}:{}'.format(alert_id, entity_id))
        redis_entities, redis_downtimes = p.execute()

        try:
            downtimes = dict((k, json.loads(v)) for (k, v) in redis_downtimes.iteritems())
        except ValueError, e:
            self.logger.exception(e)
        else:
            now = time.time()
            for uuid, d in downtimes.iteritems():
                # PF-3604 First check if downtime is active, otherwise check if it's expired, else: it's a future downtime.
                if now > d['start_time'] and now < d['end_time']:
                    d['id'] = uuid
                    result.append(d)
                    func = 'sadd'
                elif now >= d['end_time']:
                    func = 'srem'
                else:
                    continue

                # Check whether the downtime changed state: active -> inactive or inactive -> active.
                changed = getattr(self.con, func)('zmon:active_downtimes', '{}:{}:{}'.format(alert_id, entity_id, uuid))
                if changed:
                    eventlog.log(EVENTS[('DOWNTIME_ENDED' if func == 'srem' else 'DOWNTIME_STARTED')].id, **{
                        'alertId': alert_id,
                        'entity': entity_id,
                        'startTime': d['start_time'],
                        'endTime': d['end_time'],
                        'userName': d['created_by'],
                        'comment': d['comment'],
                    })

                # If downtime is over, we can remove its definition from redis.
                if func == 'srem':
                    if len(downtimes) == 1:
                        p.delete('zmon:downtimes:{}:{}'.format(alert_id, entity_id))
                        if len(redis_entities) == 1:
                            p.delete('zmon:downtimes:{}'.format(alert_id))
                            p.srem('zmon:downtimes', alert_id)
                        else:
                            p.srem('zmon:downtimes:{}'.format(alert_id), entity_id)
                    else:
                        p.hdel('zmon:downtimes:{}:{}'.format(alert_id, entity_id), uuid)
                    p.execute()

        return result
