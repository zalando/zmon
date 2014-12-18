#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime, timedelta
import base64
import json
import logging
import time
import threading
from rpc_client import get_rpc_client
from contextlib import contextmanager
import settings

from redis_context_manager import RedisConnHandler
from tasks import load_config_from_file, configure_tasks
from tasks import check_and_notify, trial_run, cleanup

logger = logging.getLogger(__name__)


TASK_POP_TIMEOUT = 5


def flow_simple_queue_processor(queue='', **execution_context):
    '''
    Simple logic to connect to a redis queue, listen to messages, decode them and execute the tasks

    :param queue: (str) queue to connect to
    :param execution_context: (dict) other kwargs that may have been passed when worker was spawn
    :return:

    Some info to understand celery messages:

    1. An example of a celery message as first received (base64-encoded body shortened):
    ('zmon:queue:default',
    '{
        "body": "eyJleHBpcm...t9fQ==", "headers": {}, "content-type": "application/json",
        "properties": {
            "body_encoding": "base64",
            "correlation_id": "check-277-de_zalando:access-control-kit-1409826332.92",
            "reply_to": "abc5c87f-74eb-3570-a1cf-e426eaf91ca7",
            "delivery_info": {
                "priority": 0,
                "routing_key": "default",
                "exchange": "zmon"
            },
            "delivery_mode": 2,
            "delivery_tag": "94288433-cb4e-4d33-be29-c63e2bbce39a"
        },
        "content-encoding": "utf-8"}'
    )

    2. An example of the message['body'] after being base64-decoded (args list shortened):
    {
        u'utc': True,
        u'chord': None,
        u'args': [{u'check_id': 277, u'interval': 60, u'entity': {u'instance_type': u'zomcat', ...}, u'condition': u'>100', ...}],
        u'retries': 0,
        u'expires': u'2014-09-04T10:27:32.919152+00:00',
        u'task': u'check_and_notify',
        u'callbacks': None,
        u'errbacks': None,
        u'timelimit': [90, 60],
        u'taskset': None,
        u'kwargs': {},
        u'eta': None,
        u'id': u'check-277-de_zalando:access-control-kit-1409826332.92'
    }

    '''

    known_tasks = {'check_and_notify': check_and_notify, 'trial_run': trial_run, 'cleanup': cleanup}

    #get configuration and configure tasks
    config = settings.get_external_config() or load_config_from_file()
    configure_tasks(config)

    logger.info('Connecting simple_queue_consumer to queue=%s, execution_context=%s', queue, execution_context)

    RedisConnHandler.configure(**dict(config))

    reactor = FlowControlReactor.get_instance()

    conn_handler = RedisConnHandler.get_instance()
    expired_count = 0
    count = 0

    while True:
        try:

            with conn_handler as ch:

                r_conn = ch.get_healthy_conn()

                encoded_task = r_conn.blpop(queue, TASK_POP_TIMEOUT)

                if encoded_task is None:
                    raise ch.IdleLoopException('No task received')

                queue, msg = encoded_task

                msg_obj = json.loads(msg)

                msg_body_enc = msg_obj['body']

                msg_body = json.loads(base64.b64decode(msg_body_enc))

                logger.debug('$$$$$$$$$$$$$$$ Got msg_body: %s', msg_body)

                taskname = msg_body['task']
                func_args = msg_body['args']
                func_kwargs = msg_body['kwargs']
                timelimit = msg_body.get('timelimit')  # [90, 60]
                t_hard, t_soft = timelimit

                # we pass task metadata as a kwargs right now, later will be put in the function context by our decorator
                task_context = {
                    'queue': queue,
                    'taskname': taskname,

                    'delivery_info': msg_obj.get('properties', {}).get('delivery_info', {}),
                    'task_properties': {
                        'task': taskname,
                        'id': msg_body.get('id', ''),
                        'expires': msg_body.get('expires'),  # '2014-09-04T10:27:32.919152+00:00'
                        'timelimit': timelimit,              # [90, 60]
                        'utc': msg_body.get('utc', True)
                    },
                }

                # discard tasks that are expired if expire metadata comes with the message
                cur_time = datetime.utcnow() if task_context['task_properties']['utc'] else datetime.now()
                expire_time = datetime.strptime(msg_body.get('expires').rsplit('+', 1)[0], '%Y-%m-%dT%H:%M:%S.%f') \
                    if msg_body.get('expires') else cur_time + timedelta(seconds=10)

                check_id = (msg_body['args'][0].get('check_id', 'xx') if len(msg_body['args']) > 0 and isinstance(msg_body['args'][0], dict) else 'XX')
                logger.debug('task loop analyzing time: check_id=%s, cur_time: %s , expire_time: %s, msg_body["expires"]=%s', check_id, cur_time, expire_time, msg_body.get('expires'))

                if cur_time < expire_time:
                    with reactor.enter_task_context(taskname, t_hard, t_soft):
                        known_tasks[taskname](*func_args, task_context=task_context, **func_kwargs)
                else:
                    logger.warn('Discarding task due to time expiration. cur_time: %s , expire_time: %s, msg_body["expires"]=%s  ----  msg_body=%s', cur_time, expire_time, msg_body.get('expires'), msg_body)
                    expired_count += 1
                    if expired_count % 500 == 0:
                        logger.warning("expired tasks count: %s", expired_count)
                count += 1

        except Exception:
            logger.exception('Exception in redis loop. Details: ')
            # some exit condition on failure: maybe when number of consecutive failures > n ?

    # TODO: Clean redis connection... very important!!!!
    # disconnect_all()


def flow_forked_child(queue='', **kwargs):
    """
    Implement forking a work horse process per message as seen in python_rq
    """
    #TODO: implement
    pass


def flow_forked_childs(queue='', **kwargs):
    """
    Implement forking several work horses process per message?
    """
    #TODO: implement
    pass


def flow_multiprocessing_pool(queue='', **kwargs):
    """
    Implement spawning a pool of workers of multiprocessing process
    """
    #TODO: implement
    pass


class FlowControlReactor(object):
    """
    Implements a singleton object with a permanently running action loop, that can communicate with the
    parent process (ProcessController) to request certain actions or submit information about the health
    of this worker.
    Only implemented capability till now is a "Hard Kill" functionality that kicks in when a task is
    taking too long to complete. We use a context manager to signal when we enter or leave this mode of operations.
    Future capabilities may include periodical reports to the parent process about number of processed tasks,
    mean time spent by the N slowest running tasks. Also a soft kill feature.
    """

    _initialized = False
    _can_init = False
    _instance = None
    t_wait = 0.2

    def __init__(self):
        #self.task_agg_info = {}  # we could aggregate some info about how tasks are running in this worker
        assert not self._initialized and self._can_init, 'Call get_instance() to instantiate'
        self._initialized = True
        self._pid = os.getpid()
        self._rpc_client = get_rpc_client('http://{}:{}{}'.format(settings.RPC_SERVER_CONF['HOST'],
                                                                   settings.RPC_SERVER_CONF['PORT'],
                                                                   settings.RPC_SERVER_CONF['RPC_PATH']))
        self._current_task_by_thread = {}  # {thread_id: (taskname, t_hard, t_soft, tstart)}
        self.action_on = False
        self._thread = threading.Thread(target=self.action_loop)
        self._thread.daemon = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._can_init = True
            cls._instance = cls()
        return cls._instance

    @contextmanager
    def enter_task_context(self, taskname, t_hard, t_soft):
        self.task_received(taskname, t_hard, t_soft)
        try:
            yield self
        except Exception as e:
            self.task_ended(exc=e)
            raise
        else:
            self.task_ended()

    def action_loop(self):

        while self.action_on:
            try:
                # hard kill logic
                for th_name, (taskname, t_hard, t_soft, ts) in self._current_task_by_thread.copy().items():
                    if time.time() > ts + t_hard:
                        logger.warn('Hard Kill request started for worker pid=%s, task: %s, t_hard=%d', self._pid,
                                    taskname, t_hard)
                        self._rpc_client.mark_for_termination(self._pid)  # rpc call to parent asking for a kill
                        self._current_task_by_thread.pop(th_name, {})
            except Exception:
                logger.exception('Scary Error in FlowControlReactor.action_loop(): ')

            time.sleep(self.t_wait)

    def start(self):
        self.action_on = True
        self._thread.start()

    def stop(self):
        self.action_on = False

    def task_received(self, taskname, t_hard, t_soft):
        # this sets a timer for this task, there is only one task per thread, and right now only main thread produce
        self._current_task_by_thread[threading.currentThread().getName()] = (taskname, t_hard, t_soft, time.time())

    def task_ended(self, exc=None):
        # delete the task from the list
        self._current_task_by_thread.pop(threading.currentThread().getName(), {})


def start_worker_for_queue(flow='simple_queue_processor', queue='zmon:queue:default', **execution_context):
    """
    Starting execution point to the workflows
    """

    known_flows = {'simple_queue_processor': flow_simple_queue_processor}

    if flow not in known_flows:
        logger.exception("Bad role: %s" % flow)
        sys.exit(1)

    logger.info("Starting worker with pid=%s, flow type: %s, queue: %s, execution_context: %s", os.getpid(), flow,
                queue, execution_context)

    # start Flow Reactor here
    FlowControlReactor.get_instance().start()

    exit_code = 0
    try:

        known_flows[flow](queue=queue, **execution_context)

    except (KeyboardInterrupt, SystemExit):
        logger.warning("Caught user signal to stop consumer: finishing!")
    except Exception:
        logger.exception("Exception in start_worker(). Details: ")
        exit_code = 2
    finally:
        FlowControlReactor.get_instance().stop()
        sys.exit(exit_code)

