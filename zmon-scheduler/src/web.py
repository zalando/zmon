#!/usr/bin/env python
# -*- coding: utf-8 -*-

from emu_celery import Celery
import datetime
from adapters import CityAdapter
from functools import partial
from itertools import chain
from emu_celery import Queue
from redis_context_manager import RedisConnHandler
from multiprocessing import Process
from pubsub import Subscriber
from schedule import Schedule
from suds.cache import ObjectCache
from suds.client import Client
from threading import Thread, RLock
from graphitesend import GraphiteClient, GraphiteSendException

import cherrypy
import json
import logging
import logging.handlers
import os
import shutil
import socket
import sys
import time
import netaddr
import heapq
import collections

from dogpile.cache import make_region
import threading
import kairosdb

logger = logging.getLogger(__name__)

DEFAULT_CACHE_EXPIRATION_TIME = 120
MAX_GRAPHITE_CONNECTION_SECS = 5
MAX_GRAPHITE_CONNECTION_REUSES = 3
SUDS_CACHE_DIR = '/tmp/suds/'


def delete_suds_cache(cache_dir):
    try:
        shutil.rmtree(cache_dir)
    except Exception:
        pass


def async_creation_runner(cache, somekey, creator, mutex):
    ''' Used by dogpile.core:Lock when appropriate '''

    def runner():
        try:
            value = creator()
            cache.set(somekey, value)
        finally:
            mutex.release()

    thread = threading.Thread(target=runner)
    thread.start()


# Asynchronous cache decorator persisted to memory.
# After the first successful invocation cache updates happen in a background thread.
async_memory_cache = make_region(async_creation_runner=async_creation_runner).configure('dogpile.cache.memory',
        expiration_time=DEFAULT_CACHE_EXPIRATION_TIME)


class PropertiesEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class ZmonScheduler(Process):

    DEFAULT_CHECK_INTERVAL = 60
    DEFAULT_UPDATE_INTERVAL = 254
    METRICS_UPDATE_INTERVAL = 15
    RESULTS_KEY_EXPIRY_TIME = 286
    CAPTURES_UPDATE_INTERVAL = 15
    LOG_COUNT_CHECK_INTERVAL = 10
    DEFAULT_CLEANUP_INTERVAL = 317

    # Since we store teams in a set and use plural as the key, we need to map the entity definition to the actual value.
    # If we decide to add more complex entity definitions, we can always extend this map.
    ENTITY_KEY_MAP = {'team': 'teams'}

    # special global pseudo entity
    GLOBAL_ENTITY = {'id': 'GLOBAL', 'type': 'GLOBAL'}

    DOWNTIME_SCHEDULE_PUBSUB = 'zmon:downtime_schedule:pubsub'
    DOWNTIME_SCHEDULE_EXCHANGE = 'zmon:downtime_schedule:requests'
    DOWNTIME_REMOVE_PUBSUB = 'zmon:downtime_remove:pubsub'
    DOWNTIME_REMOVE_EXCHANGE = 'zmon:downtime_remove:requests'
    TRIAL_RUN_PUBSUB = 'zmon:trial_run:pubsub'
    TRIAL_RUN_EXCHANGE = 'zmon:trial_run:requests'
    INSTANT_EVAL_PUBSUB = 'zmon:alert_evaluation:pubsub'
    INSTANT_EVAL_EXCHANGE = 'zmon:alert_evaluation:requests'

    @property
    def redis_connection(self):
        return RedisConnHandler.get_instance().get_conn()

    @property
    def ws_client(self):
        if self._ws_client is None:
            try:
                # maybe this fixes suds cache: stackoverflow.com/questions/6153652/suds-ignoring-cache-setting
                oc = ObjectCache()
                oc.setduration(seconds=300)
                self._ws_client = Client(url=cherrypy.config.get('zmon.url'), cache=oc, timeout=300)
            except Exception:
                self.logger.warn('Failed to connect to zmon-controller')
                raise
        return self._ws_client

    def _disconnect_graphite(self):
        try:
            if self._graphite_client is not None:
                self._graphite_client.disconnect()
        except:
            self.logger.exception('Failed disconnect Graphite Server, GC will close connection eventually')
        self._graphite_client = None

    def graphite_client_get(self):
        with self._graphite_conn_lock:
            if self._graphite_client is None or time.time() - self._last_graphite_connect \
                > MAX_GRAPHITE_CONNECTION_SECS or self._graphite_conn_reuse_count > MAX_GRAPHITE_CONNECTION_REUSES:
                self._disconnect_graphite()
                config = cherrypy.config
                self._graphite_client = GraphiteClient(graphite_server=config.get('graphite.host'),
                                                       graphite_port=config.get('graphite.port', 2003),
                                                       prefix=config.get('graphite.prefix', 'zmon2'), system_name='')
                self._last_graphite_connect = time.time()
                self._graphite_conn_reuse_count = 0
            else:
                self._graphite_conn_reuse_count += 1
            return self._graphite_client

    def graphite_client_set(self, value):
        with self._graphite_conn_lock:
            self._disconnect_graphite()
            self._graphite_client = (value if isinstance(value, GraphiteClient) else None)

    graphite_client = property(graphite_client_get, graphite_client_set)

    def __init__(self, parentPID, app, instance_code='local', host='unknown', loglevel=logging.INFO):
        super(ZmonScheduler, self).__init__()

        self.check_definitions = {}
        self.alert_definitions = {}
        self.check_alert_map = {}
        self.schedule = Schedule()

        self.count_checks_per_queue = {}
        self.count_checks_per_queue_last_cleaned = None

        # A list of all active adapters and adapter -> entity type mapping.
        self.adapters = {
                'cities': ['city'],
        }

        # These two should be set to None in case initial checks/alerts request fails. After update starts, passing
        # None as snapshot id will fetch all entries from the web service.
        self.checks_snapshot = None
        self.alerts_snapshot = None

        self.app = app
        self.parentPID = parentPID
        self.instance_code = instance_code
        self.host = host

        # TODO: make entity adapters dynamic (pluggable)
        self.cities = CityAdapter(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'cities.json')))

        self.run_using_heap = cherrypy.config.get('scheduler.use_heap')

        self.safe_repositories = [repo.rstrip('/') + '/' for repo in cherrypy.config.get('safe_repositories', [])]

        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger('zmon-scheduler')
        self.logger.setLevel(loglevel)

        #self._redis_connection = None
        self._graphite_client = None
        self._ws_client = None
        self.pubsub_initialized = False

        self._last_graphite_connect = 0
        self._graphite_conn_reuse_count = 0
        self._graphite_conn_lock = RLock()

        l = cherrypy.config.get('queue.snmp.check_ids')
        if l is not None:
            if not isinstance(l, collections.Iterable):
                l = [l]
            self._snmp_check_ids = set(map(lambda x: str(x), l))
        else:
            self._snmp_check_ids = set()

        l = cherrypy.config.get('queue.internal.check_ids')
        if l is not None:
            if not isinstance(l, collections.Iterable):
                l = [l]
            self._internal_check_ids = set(map(lambda x: str(x), l))
        else:
            self._internal_check_ids = set()

        self.logger.info("snmp ids: %s", self._snmp_check_ids)
        self.logger.info("internal ids: %s", self._internal_check_ids)

        kairosdb.setLogger(logger)
        kairosdb.setKairosDB(cherrypy.config.get('kairosdb.host'), cherrypy.config.get('kairosdb.port'),
                             cherrypy.config.get('kairosdb.env'))

        self.update_checks_thread = Thread(target=self._update_check_definitions, name='update_checks_thread')
        self.update_checks_thread.daemon = True
        self.update_alerts_thread = Thread(target=self._update_alert_definitions, name='update_alerts_thread')
        self.update_alerts_thread.deamon = True
        self.update_metrics_thread = Thread(target=self._update_metrics, name='update_metrics_thread')
        self.update_metrics_thread.daemon = True
        self.update_captures_thread = Thread(target=self._update_captures2graphite, name='update_captures_thread')
        self.update_captures_thread.daemon = True
        self.update_properties_thread = Thread(target=self._update_properties, name='update_properties_thread')
        self.update_properties_thread.daemon = True

        checks_thread = Thread(target=self._load_check_definitions, name='checks_thread')
        alerts_thread = Thread(target=self._load_alert_definitions, name='alerts_thread')

        checks_thread.start()
        alerts_thread.start()


        self.heap = []
        # mark forced executions to skip one execution
        self.mark_as_skip = {}
        self.cache_check_route = {}

        for adapter in self.adapters:
            if adapter != 'hosts':
                getattr(self, adapter).load_thread.start()

        checks_thread.join()
        alerts_thread.join()
        for adapter in self.adapters:
            if adapter != 'hosts':
                getattr(self, adapter).load_thread.join()

        # Initialization of cleanup dict
        # Cleanup dict consists of two parts: disabled checks/alerts and currently active checks/alerts. The disabled
        # part is updated every time we get an update from the webservice. The active part is generated on startup and
        # updated when we get changes from webservice or other data provider (cmdb, deployctl, config service).
        # The active part is a simple dict with check/alert ids as keys and lists of matching entity ids as values.
        self.cleanup = {'disabled_checks': set([]), 'disabled_alerts': set([])}

    def _add_to_count_checks(self, routing_key, number):
        self.count_checks_per_queue[routing_key] = self.count_checks_per_queue.get(routing_key, 0) + number

    def _periodical_log_count_checks(self):
        # periodically log aggregated info: number of checks scheduled by queue
        cur_time = time.time()
        if self.count_checks_per_queue_last_cleaned is None:
            self.count_checks_per_queue_last_cleaned = cur_time

        if cur_time - self.count_checks_per_queue_last_cleaned >= self.LOG_COUNT_CHECK_INTERVAL:
            self.logger.info('Count of checks scheduled in the last %d seconds: %s', self.LOG_COUNT_CHECK_INTERVAL,
                             self.count_checks_per_queue)

            kv = []
            for k, n in self.count_checks_per_queue.iteritems():
                kv.append(kairosdb.get_kairosdb_value('zmon.scheduled.checks', cur_time, n, {'queue': k}))

            self.count_checks_per_queue = {}
            self.count_checks_per_queue_last_cleaned = cur_time

            kairosdb.write_to_kairosdb(kv)

    @staticmethod
    def __map_entities(entities):
        """
        Convert entities from nested SOAP objects to plain dict.
        From:
        [(entity){
          attributes =
             (attributes){
                attribute[] =
                   (entityAttribute){
                      key = "type"
                      value = "zomcat"
                   },
             }
        }]
        to:
        [{type: zomcat}]
        """

        return [dict((key_value.key, (key_value.value if isinstance(key_value.value,
                basestring) else str(key_value.value))) for key_value in attribute.attributes.attribute) for entity in
                entities for attribute in entity[1]]

    @staticmethod
    def __map_alert_definition(alert):
        # PF-2598 It's more convenient to map period to empty string because empty string evaluates to True in
        # in_period function (see tasks.py in zmon-scheduler).
        alert_notifications = (Client.dict(alert.notifications) if hasattr(alert, 'notifications') else {})
        alert_parameters = (json.loads(alert.parameters) if hasattr(alert, 'parameters') else {})
        entities_map = (ZmonScheduler.__map_entities(alert.entities) if hasattr(alert, 'entities') else [])
        entities_exclude_map = (ZmonScheduler.__map_entities(alert.entitiesExclude) if hasattr(alert, 'entitiesExclude'
                                ) else [])
        return {
            'id': alert.id,
            'check_id': alert.checkDefinitionId,
            'name': alert.name,
            'team': alert.team,
            'condition': alert.condition,
            'notifications': alert_notifications.get('notification', []),
            'entities_map': entities_map,
            'entities_exclude_map': entities_exclude_map,
            'responsible_team': alert.responsibleTeam,
            'priority': alert.priority,
            'period': (alert.period or '' if hasattr(alert, 'period') else ''),
            'parameters': alert_parameters,
        }

    def _load_check_definitions(self):
        self.logger.info('Fetching check definitions')

        try:
            response = self.ws_client.service.getAllActiveCheckDefinitions()
        except Exception:
            self.logger.exception('Failed to load initial check definitions')
        else:
            self.checks_snapshot = response[0]
            for c in response[1]:
                c.entities_map = (self.__map_entities(c.entities) if hasattr(c, 'entities') else [])
                c.entities_exclude_map = (self.__map_entities(c.entitiesExclude) if hasattr(c, 'entitiesExclude'
                                          ) else [])
                self.check_definitions[c.id] = c
            self.logger.info('Got %s check definition(s)', len(self.check_definitions))

    def _load_alert_definitions(self):
        self.logger.info('Fetching alert definitions')
        try:
            response = self.ws_client.service.getAllActiveAlertDefinitions()
        except Exception:
            self.logger.exception('Failed to load initial alert definitions')
        else:
            self.alerts_snapshot = response[0]
            self.alert_definitions = dict((a.id, self.__map_alert_definition(a)) for a in response[1])
            for _id, alert in self.alert_definitions.iteritems():
                if alert['check_id'] in self.check_alert_map:
                    self.check_alert_map[alert['check_id']].add(_id)
                else:
                    self.check_alert_map[alert['check_id']] = set([_id])
            self.logger.info('Got %s alert definition(s)', len(self.alert_definitions))

    def _update_check_definitions(self):
        self._checks_update_running = True
        while self._checks_update_running:
            time.sleep(self.DEFAULT_UPDATE_INTERVAL)
            if not self._checks_update_running:
                return
            self.logger.info('Updating check definitions with snapshot %s', self.checks_snapshot)
            try:
                response = self.ws_client.service.getCheckDefinitionsDiff(self.checks_snapshot)
            except Exception:
                self.logger.warn('Failed to update check definitions with snapshot %s', self.checks_snapshot,
                                 exc_info=True)
            else:
                self.checks_snapshot = response.snapshotId
                self.logger.info('Got new snapshot for check definitions %s', self.checks_snapshot)

                if hasattr(response, 'changedDefinitions') and response.changedDefinitions:
                    self.logger.info('Got %s new check definition(s)', len(response.changedDefinitions[0]))
                    for d in response.changedDefinitions[0]:
                        d.entities_map = (self.__map_entities(d.entities) if hasattr(d, 'entities') else [])
                        d.entities_exclude_map = (self.__map_entities(d.entitiesExclude) if hasattr(d, 'entitiesExclude'
                                                  ) else [])
                        self.check_definitions[d.id] = d

                        # queue for execution (not perfect, expensive check can by chance run twice)
                        if self.run_using_heap:
                            self.mark_as_skip[d.id] = 1
                            heapq.heappush(self.heap, (0, d.id))

                        self.logger.info('got updated check_def with id=%s, %s, %s', d.id, d.entities_map,
                                         d.entities_exclude_map)

                if hasattr(response, 'disabledDefinitions') and response.disabledDefinitions:
                    self.logger.info('Got %s disabled check definition(s)',
                                     len(response.disabledDefinitions.disabledDefinition))
                    for d in response.disabledDefinitions.disabledDefinition:
                        self.cleanup['disabled_checks'].add(d)
                        if d in self.check_alert_map:
                            for alert_id in self.check_alert_map[d]:
                                self.cleanup['disabled_alerts'].add(alert_id)
                            del self.check_alert_map[d]
                        if d in self.check_definitions:
                            del self.check_definitions[d]

    def _update_alert_definitions(self):
        self._alerts_update_running = True
        while self._alerts_update_running:
            time.sleep(self.DEFAULT_UPDATE_INTERVAL)
            if not self._alerts_update_running:
                return
            self.logger.info('Updating alert definitions with snapshot %s..', self.alerts_snapshot)
            try:
                response = self.ws_client.service.getAlertDefinitionsDiff(self.alerts_snapshot)
            except Exception:
                self.logger.warn('Failed to update alert definitions with snapshot %s', self.alerts_snapshot,
                                 exc_info=True)
            else:
                self.alerts_snapshot = response.snapshotId
                self.logger.info('Got new snapshot for alert definitions %s', self.alerts_snapshot)

                if hasattr(response, 'changedDefinitions') and response.changedDefinitions:
                    self.logger.info('Got %s new alert definition(s)', len(response.changedDefinitions[0]))
                    for a in response.changedDefinitions[0]:
                        self.alert_definitions[a.id] = self.__map_alert_definition(a)
                        # Check definition already exists.
                        self.logger.info('got updated alert_def with id=%s, %s, %s', a.id,
                                         self.alert_definitions[a.id]['entities_map'],
                                         self.alert_definitions[a.id]['entities_exclude_map'])
                        if a.checkDefinitionId in self.check_alert_map:
                            # New alert definition for existing check.
                            if a.id not in self.check_alert_map[a.checkDefinitionId]:
                                self.check_alert_map[a.checkDefinitionId].add(a.id)
                        else:
                            # New check definition and new alert definition.
                            self.check_alert_map[a.checkDefinitionId] = set([a.id])

                if hasattr(response, 'disabledDefinitions') and response.disabledDefinitions:
                    self.logger.info('Got %s disabled alert definition(s)',
                                     len(response.disabledDefinitions.disabledDefinition))
                    for d in response.disabledDefinitions.disabledDefinition:
                        self.cleanup['disabled_alerts'].add(d)
                        # Remove single alert definitions ids from check-alert mapping.
                        for alert_ids in self.check_alert_map.itervalues():
                            if d in alert_ids:
                                alert_ids.remove(d)
                        # Remove checks without alerts (first generate list of keys to remove, then remove them).
                        for check_id in [k for (k, v) in self.check_alert_map.items() if len(v) == 0]:
                            del self.check_alert_map[check_id]
                        # Remove alert definition
                        if d in self.alert_definitions:
                            del self.alert_definitions[d]

    def _update_metrics(self):
        config = cherrypy.config
        data = {}
        last_time = 0
        while True:
            time.sleep(self.METRICS_UPDATE_INTERVAL)
            update_start = time.time()
            self.logger.info('Sending metrics to Graphite..')
            try:
                workers = self.redis_connection.smembers('zmon:metrics')
                new_data = {}
                now = time.time()

                for worker in workers:
                    keys = set(['check.count'])
                    for check_id, alert_ids in self.check_alert_map.items():
                        keys.add('check.{}.count'.format(check_id))
                        keys.add('check.{}.duration'.format(check_id))
                        keys.add('check.{}.latency'.format(check_id))
                        for alert_id in list(alert_ids):
                            keys.add('alerts.{}.count'.format(alert_id))
                            keys.add('alerts.{}.evaluation_duration'.format(alert_id))
                            keys.add('alerts.{}.notification_duration'.format(alert_id))

                    p = self.redis_connection.pipeline()
                    for key in keys:
                        p.get('zmon:metrics:{}:{}'.format(worker, key))
                    metrics = p.execute()

                    for key, metric in zip(keys, metrics):
                        if metric:
                            new_data['{}.{}'.format(worker.replace('.', '_'), key)] = int(metric)

                if data:
                    diff = {}
                    delta = now - last_time
                    for k, v in new_data.items():
                        diff[k] = (v - data.get(k, 0)) / delta
                    if config.get('graphite.allow_push_metrics', True):
                        self.graphite_client.send_dict(diff)
                data = new_data
                last_time = now
            except GraphiteSendException:
                self.graphite_client = None
                self.logger.exception('Failed to update metrics... Forcing reconnect to Graphite Server')
            except:
                self.logger.exception('Failed to update metrics')
            self.logger.info('Sent metrics to Graphite, duration: %.3fs', time.time() - update_start)

    def _update_captures2graphite(self):
        config = cherrypy.config
        while True:
            time.sleep(self.CAPTURES_UPDATE_INTERVAL)
            try:
                captures_json = self.redis_connection.lrange('zmon:captures2graphite', 0, -1)
                if captures_json:
                    if config.get('graphite.allow_push_captures', False):
                        self.logger.info('Sending %d captures to Graphite', len(captures_json))
                        self.graphite_client.send_list(filter(lambda l: None not in l, [json.loads(c) for c in
                                                       captures_json]))
                    self.redis_connection.ltrim('zmon:captures2graphite', len(captures_json), -1)
            except GraphiteSendException:
                self.graphite_client = None
                self.logger.exception('Failed to update metrics... Forcing reconnect to Graphite Server')
            except:
                self.logger.exception('Failed to copy captures to graphite')

    def _schedule_trial_runs(self, request):
        request_count = 0
        id_ = 'TR:{}'.format(request['id'])
        redis_key = 'zmon:trial_run:{uuid}'.format(uuid=request['id'])
        name = request['name']
        check_command = request['check_command']
        alert_condition = request['alert_condition']
        requested_entities = request['entities']
        created_by = request['created_by']
        # Interval should be mandatory now, in case we don't receive it, we set one minute as default.
        # The check won't be executed periodically anyway, but this value will be used as time limit.
        interval = request.get('interval', self.DEFAULT_CHECK_INTERVAL)
        # NOTE If the client sends 'null' as time period, it'll be converted to None and get will return
        # this value.
        period = request.get('period') or ''
        parameters = request.get('parameters', {})
        entities_map = request.get('entities', [])
        entities_exclude_map = request.get('entities_exclude', [])
        # generate entities but make sure to refresh the cache just in case
        entities = self._generate_check_entities.refresh(self, {'id': id_, 'entities_map': entities_map,
                                                         'entities_exclude_map': entities_exclude_map}, True)

        alert = {
            'id': id_,
            'check_id': id_,
            'name': name,
            'team': 'TRIAL RUN',
            'condition': alert_condition,
            'notifications': (),
            'entities_map': requested_entities,
            'responsible_team': 'TRIAL RUN',
            'priority': 3,
            'period': period,
            'parameters': parameters,
        }

        options = {
            'soft_time_limit': interval,
            'expires': 2 * interval,
            'queue': 'zmon:queue:internal',
            'routing_key': 'internal',
        }

        try:
            p = self.redis_connection.pipeline()
            for entity in entities:
                # Sadly, SADD with multiple arguments isn't supported until Redis 2.4.
                self.logger.info('Making trial run requests with id %s', id_)
                p.sadd(redis_key, entity['id'])
                req = {
                    'command': check_command,
                    'entity': entity,
                    'check_id': id_,
                    'check_name': name,
                    'interval': interval,
                    'created_by': created_by,
                }
                task = self.app.signature('trial_run', args=(req, [alert]), options=options)
                task.apply_async(task_id='check-{}-{}-{:.2f}'.format(id_, entity['id'], time.time()))
                request_count += 1

            if request_count:
                self.logger.info('Trial run created %s request(s)', request_count)
                p.expire(redis_key, self.RESULTS_KEY_EXPIRY_TIME)
            else:
                self.logger.warn('No entities for trial run: %s, with entities: %s', name, requested_entities)

            p.hdel('zmon:trial_run:requests', request['id'])
            p.execute()
        except Exception, e:
            self.logger.warn('Failed to update the trial runs')
            self.logger.exception(e)

    def _schedule_downtime(self, downtime):
        alert_id = downtime['alert_definition_id']

        if alert_id in self.alert_definitions and self.alert_definitions[alert_id]['check_id'] in self.check_alert_map:
            self.logger.info('Scheduling downtime for alert %s', alert_id)
            self.schedule.set_downtime(self.alert_definitions[alert_id]['check_id'], downtime['id'],
                                       downtime['start_time'], downtime['end_time'])
        else:
            self.logger.warn('Downtime request without active checks for alert id %s', alert_id)

    def _remove_downtime(self, downtime):
        alert_id = downtime['alert_definition_id']

        if alert_id in self.alert_definitions and self.alert_definitions[alert_id]['check_id'] in self.check_alert_map:
            check_id = self.alert_definitions[alert_id]['check_id']
            self.logger.info('Removing downtime for check %s, alert %s', check_id, alert_id)
            self.schedule.remove_downtime(check_id, downtime['id'], int(self.check_definitions[check_id].interval))
        else:
            self.logger.warn('Downtime removal request without active checks for alert id %s', alert_id)

    def _force_check_eval(self, request):
        alert_id = request['alert_definition_id']

        if alert_id in self.alert_definitions and self.alert_definitions[alert_id]['check_id'] in self.check_alert_map:
            check_id = self.alert_definitions[alert_id]['check_id']
            self.logger.info('Marking for immediate evaluation check %s, alert %s', check_id, alert_id)

            if self.run_using_heap:
                # real "instant" eval
                self.mark_as_skip[check_id] = 1
                heapq.heappush(self.heap, (0, check_id))
            else:
                self.schedule.mark_for_run(check_id)


        else:
            self.logger.warn('Non-valid alert id %s received in immediate evaluation request', alert_id)

    def _update_properties(self):
        while True:
            time.sleep(self.DEFAULT_UPDATE_INTERVAL)
            self.logger.info('Updating entities properties in redis')
            properties = dict((t, getattr(self, adapter).properties()) for (adapter, types) in
                              self.adapters.iteritems() for t in types)
            try:
                self.redis_connection.set('zmon:entity:properties', json.dumps(properties, cls=PropertiesEncoder))
            except Exception:
                self.logger.exception('Failed to update entities properties in redis')

    @staticmethod
    def _compare_entity(entity, key, value):
        '''
        >>> ZmonScheduler._compare_entity({'type': 'host'}, 'type', 'host')
        True

        >>> ZmonScheduler._compare_entity({'project': 'shop'}, 'environment', 'live')
        False

        >>> ZmonScheduler._compare_entity({'teams': set(['Shop', 'Article'])}, 'team', 'Shop')
        True

        >>> ZmonScheduler._compare_entity({'type': 'host', 'internal_ip': '10.10.10.10'}, 'internal_ip', '10.10.10.10')
        True

        >>> ZmonScheduler._compare_entity({'type': 'host', 'external_ip': '10.10.10.10'}, 'internal_ip', '10.10.10.10')
        False

        >>> ZmonScheduler._compare_entity({'type': 'host', 'internal_ip': '10.10.10.10'}, 'internal_ip', '10.10.10.0/24')
        True

        >>> ZmonScheduler._compare_entity({'type': 'host', 'internal_ip': '10.12.10.10'}, 'internal_ip', '10.10.0.0/16')
        False

        >>> ZmonScheduler._compare_entity({'type': 'host', 'internal_ip': 'NOT_AN_IP'}, 'internal_ip', '10.10.0.0/16')
        False
        '''

        # we need this, in any case entity.get(key) != value ... which is quite likely:
        ips = None
        if entity.get('type') == 'host' and key in ('internal_ip', 'external_ip'):
            # first try to build an IPSet, return False if this fails..., we can't compare anyway
            try:
                netaddr.IPSet([entity.get(key)])
                ips = netaddr.IPSet([value])
            except:
                logger.warn('host entity: %s IP compare failed!', entity.get('host', '-no-name-'))
                return False

        return (value in entity[ZmonScheduler.ENTITY_KEY_MAP[key]] if key in ZmonScheduler.ENTITY_KEY_MAP
                and ZmonScheduler.ENTITY_KEY_MAP[key] in entity else entity.get(key) == value or bool(ips)
                and entity.get(key, '0.0.0.0/32') in ips)

    @async_memory_cache.cache_on_arguments(namespace='zmon-scheduler')
    def _generate_check_entities(self, check_def, is_trial_run):

        entities = []

        # self.logger.info('_generate_check_entities() called for check_id=%s', check_def['id'])

        has_alerts = check_def['id'] in self.check_alert_map

        if not has_alerts and not is_trial_run:  # do not schedule checks without alerts unless is trial run
            return []

        all_entities = list(chain(chain(*(getattr(self, a).entities for a in self.adapters)), [self.GLOBAL_ENTITY]))
        entities_by_id = dict([(self.get_or_generate_entity_id(entity), entity) for entity in all_entities])

        entities_check_level = self._filter_entities(all_entities, check_def['entities_map'])
        positive_entities_ids = set(self.get_or_generate_entity_id(e) for e in entities_check_level)

        # entities_exclude_check_level = self._filter_entities(all_entities, check_def['entities_exclude_map'])
        entities_exclude_check_level = []
        negative_entities_ids = set(self.get_or_generate_entity_id(e) for e in entities_exclude_check_level)

        _matching_entities_ids = set()

        # self.logger.debug('_generate_check_entities(): check_id=%s, entities_map=%s, positive_entities_ids=%s, entities_exclude_map=%s, negative_entities_ids=%s'
        #                  , check_def['id'], check_def['entities_map'], positive_entities_ids,
        #                  check_def['entities_exclude_map'], negative_entities_ids)

        # Additional filtering of entities based on filters defined in alert definitions.
        if has_alerts:

            for alert_id in list(self.check_alert_map[check_def['id']]):

                # positive entity filtering
                alert_entities_map = self.alert_definitions[alert_id]['entities_map']
                filtered_entities = (self._filter_entities(entities_check_level,
                                     alert_entities_map) if alert_entities_map else entities_check_level)
                # ids that match positive filter
                posi_ids = set(self.get_or_generate_entity_id(e) for e in filtered_entities)

                # self.logger.debug('_generate_check_entities(): alert_id=%s, alert_entities_map=%s, posi_ids=%s',
                #                  alert_id, alert_entities_map, posi_ids)

                # negative entity filtering
                alert_entities_exclude_map = self.alert_definitions[alert_id].get('entities_exclude_map', [])
                negative_filtered_entities = self._filter_entities(entities_check_level, alert_entities_exclude_map)
                # ids that match negative filter
                nega_ids = set(self.get_or_generate_entity_id(e) for e in negative_filtered_entities)

                # entities ids that match this alert
                posi_ids = posi_ids - nega_ids

                # self.logger.debug('_generate_check_entities(): alert_id=%s, alert_entities_exclude_map=%s, nega_ids=%s'
                #                  , alert_id, alert_entities_exclude_map, nega_ids)
                # self.logger.debug('_generate_check_entities(): alert_id=%s, final_entities_ids=%s', alert_id, posi_ids)

                # negative_entity_ids.update(set(self.get_or_generate_entity_id(e) for e in negative_filtered_entities))

                _matching_entities_ids.update(posi_ids)

            _matching_entities_ids = _matching_entities_ids - negative_entities_ids
        elif is_trial_run:

            # trial run are executed even if they have no alerts
            _matching_entities_ids = positive_entities_ids - negative_entities_ids

        # self.logger.debug('_generate_check_entities(): check_id=%s, final_entities_ids=%s', check_def['id'],
        #                  _matching_entities_ids)

        _matching = [entities_by_id[_id] for _id in _matching_entities_ids]

        for m in _matching:
            # NOTE We need to store the team info in a set for quick membership queries, but we cannot
            # serialize sets to JSON. That's why we create a copy of an entity and change teams to a list.
            entity = m.copy()
            if 'teams' in entity:
                entity['teams'] = list(entity['teams'])
            entities.append(entity)

        return entities

    @staticmethod
    def _filter_entities(entity_list, entities_map):
        """
        Filters a list of entities with the entities_map filter.
        An example entities_map filter is: [{type: zompy, environment: integration}, {type:zomcat, environment: live}]
        Which means: (type -> zompy AND environment -> integration) OR (type -> zomcat AND environment -> live)

        >>> ZmonScheduler._filter_entities([{'id': 1, 'type': 'zompy'}], [])
        []

        >>> ZmonScheduler._filter_entities([{'type': 'a'}, {'type': 'b'}], [{'type': 'a'}])
        [{'type': 'a'}]
        """

        _matching = []

        for entity in entity_list or []:
            for entity_def in entities_map or []:
                if all(ZmonScheduler._compare_entity(entity, k, v) for (k, v) in entity_def.iteritems()):
                    _matching.append(entity)
                    break
        return _matching

    @staticmethod
    def _alert_matches_entity(alert, entity):
        '''
        >>> ZmonScheduler._alert_matches_entity({'entities_map': []}, {'id': 1})
        True

        >>> ZmonScheduler._alert_matches_entity({'entities_map': [{'type': 'a'}]}, {'type': 'b'})
        False
        '''

        entities_map = alert.get('entities_map', [])
        entities_exc_map = alert.get('entities_exclude_map', [])

        match_pos = (bool(ZmonScheduler._filter_entities([entity], entities_map)) if entities_map else True)
        match_neg = bool(ZmonScheduler._filter_entities([entity], entities_exc_map))
        try:
            logger.debug('_alert_matches_entity(): alert_id=%s, entities_map=%s, entities_exc_map=%s, match_pos=%s, match_neg=%s'
                         , alert['id'], entities_map, entities_exc_map, match_pos, match_neg)
        except Exception:
            logger.exception('Error when trying to log log: ')
        return match_pos and not match_neg

    @async_memory_cache.cache_on_arguments(namespace='zmon-scheduler', expiration_time=30)
    def _generate_alerts(self, entity, check_id):
        """
        Filters alert definitions based on the entity being checked. See unit tests for detailed explanation.
        Parameters
        ----------
        entity: dict
            Instance/host to check alert definitions against.
        check_id: int
            Id of check definition for given entity.
        Returns
        -------
        list
            A list of alert definitions matching given entity.
        """

        # TODO: see if lowering the cache time as we have done help in the exclude filter
        # self.logger.debug('calling _generate_alerts() with entity: %s , check_id: %s', entity, check_id)
        # PF-3888 If the alert gets removed while generating check entities, we will get an exception here. We create a
        # copy using list because it's faster than calling set.copy().
        return filter(partial(self._alert_matches_entity, entity=entity), [self.alert_definitions[i] for i in
                      list(self.check_alert_map[check_id])])

    def get_or_generate_entity_id(self, entity):
        _id = entity.get('id')
        if _id is not None:
            return _id
        else:
            self.logger.warn('Encountered entity without id: %s. Trying to generate an id', entity)
            try:
                return str(entity)
            except Exception:
                self.logger.error('Unable to generate id for entity')
                return None

    def _run_cleanup(self):
        self.logger.info('Starting cleanup task')
        start_cleanup = datetime.datetime.now()

        if self.check_definitions and self.alert_definitions:
            # This should be improved, it's definitely not the fastest way to update matching entity ids, e.g. if only
            # one host was decommissioned in CMDB, we will iterate through all host entities, instead of just removing
            # the decommissioned one.
            check_entities = dict((k, list(self._generate_check_entities(v, False))) for (k, v) in
                                  self.check_definitions.items())
            self.cleanup['check_entities'] = dict((k, [e['id'] for e in v]) for (k, v) in check_entities.items())
            self.cleanup['alert_entities'] = dict((k, [e['id'] for e in check_entities[v['check_id']]
                                                  if self._alert_matches_entity(v, e)]) for (k, v) in
                                                  self.alert_definitions.items() if v['check_id'] in check_entities)

            kwargs = {
                'disabled_checks': list(self.cleanup['disabled_checks']),
                'disabled_alerts': list(self.cleanup['disabled_alerts']),
                'check_entities': self.cleanup['check_entities'],
                'alert_entities': self.cleanup['alert_entities'],
            }

            cleanup = self.app.signature('cleanup', options={'expires': self.DEFAULT_UPDATE_INTERVAL,
                                         'queue': 'zmon:queue:internal', 'routing_key': 'internal'}, kwargs=kwargs)
            try:
                cleanup.apply_async(task_id='cleanup-{:.2f}'.format(time.time()))
            except Exception, e:
                self.logger.exception(e)

            self.cleanup['disabled_checks'].clear()
            self.cleanup['disabled_alerts'].clear()
        else:
            self.logger.info('Skipping cleanup task. No checks and alerts definitions')

        end_cleanup = datetime.datetime.now()
        self.logger.info('Cleanup scheduling took {}'.format(end_cleanup - start_cleanup))

    @async_memory_cache.cache_on_arguments(namespace='zmon-scheduler')
    def get_queue_and_routing_key(self, check_definition):
        # pick the right queue
        if check_definition.name.startswith('ZMON') or (hasattr(check_definition, 'id') and str(check_definition.id) in self._internal_check_ids):
            queue, routing_key = 'zmon:queue:internal', 'internal'
        elif hasattr(check_definition, 'sourceUrl') and any(check_definition.sourceUrl.startswith(r) for r in
                                                            self.safe_repositories):

            queue, routing_key = 'zmon:queue:secure', 'secure'
        elif hasattr(check_definition, 'id') and str(check_definition.id) in self._snmp_check_ids:
            queue, routing_key = 'zmon:queue:snmp', 'snmp'
        else:
            queue, routing_key = 'zmon:queue:default', 'default'
        return queue, routing_key

    def execute_check(self, check):
        interval = int(check.interval)
        expires = 2 * interval
        queue, routing_key = self.get_queue_and_routing_key(check)
        number_of_requests = 0

        for entity in self._generate_check_entities(check, False):
            req = {
                'command': check.command,
                'entity': entity,
                'check_id': check.id,
                'check_name': check.name,
                'interval': interval,
                'schedule_time': time.time(),
            }

            options = {
                'soft_time_limit': min(interval, 60 * 7),
                'time_limit': min(interval, 60 * 7) + 30,
                'expires': expires,
                'queue': queue,
                'routing_key': routing_key,
            }

            try:
                number_of_requests += 1
                task = self.app.signature('check_and_notify', args=(req, self._generate_alerts(entity,
                                                                                               check.id)), options=options)
                task.apply_async(task_id='check-{}-{}-{:.2f}'.format(check.id, entity['id'], time.time()))
            except Exception, e:
                self.logger.exception(e)

        if not number_of_requests:
            if check.id in self.check_alert_map:

                # remove entities from redis for that check and alerts,
                # otherwise user gets no feedback about wrong entity filter

                p = self.redis_connection.pipeline()
                p.delete('zmon:checks:{}'.format(check.id))
                for alert_id in list(self.check_alert_map[check.id]):
                    p.delete('zmon:alerts:{}:entities'.format(alert_id))

                p.execute()

                self.logger.info('No matching entities for check: %s id %s', check.name, check.id)
            else:
                self.logger.debug('No alerts defined for check: %s id %s', check.name, check.id)
        else:
            self._add_to_count_checks(routing_key, number_of_requests)
            self._periodical_log_count_checks()


    """

    using a heap queue for determining the next checks to be executes, we store next executing time for the sorting and check id

    TODO:
     * changed checks executed immediately, try to cancel/move next execution
     * remove legacy partitioning

    """
    def build_heap(self):
        self.logger.info("Start build of heap")

        items = 0
        for check in self.check_definitions.values():
            #legacy partition, needs to be removed if scheduler is fast enough again
            if self.instance_code in ['3422', '3423']:
                if self.instance_code == '3423' and check.interval > 30:
                    continue
                elif self.instance_code == '3422' and check.interval <= 30:
                    continue
                else:
                    pass

            next_run = self.schedule.get_next_time(check.id, check.interval)
            entry = (next_run, check.id)
            items += 1
            heapq.heappush(self.heap, entry)

        self.logger.info("Done building heap ... %s", items)

    def run_heap_scheduler(self):

        self.logger.info("Running using heap scheduler ...")

        while not self.check_definitions or not self.schedule.loaded:
            if self.check_definitions and not self.schedule.loaded:
                self.schedule.load(self.check_definitions)

        # self.build_heap()

        while True:
            # fetch next check from heap, if in future push back and sleep, otherwise execute
            now = time.time()
            (exec_time, check_id) = heapq.heappop(self.heap)

            if exec_time > now:
                heapq.heappush(self.heap, (exec_time, check_id))
                if (exec_time - now) > 0.5:
                    self.logger.info("... scheduler sleep %s", (exec_time - now))
                    time.sleep(0.2)
                continue

            # skip one execution of check after updated/forced execution
            if check_id in self.mark_as_skip:
                v = self.mark_as_skip[check_id]
                if v == 1:
                    self.mark_as_skip[check_id] = 0
                else:
                    self.logger.info("Skipping execution ... %s", check_id)
                    del self.mark_as_skip[check_id]
                    continue

            # execute check, store in schedule and push back into queue
            if check_id in self.check_definitions:
                check = self.check_definitions[check_id]
                if check is None:
                    del self.check_definitions[check_id]
                    continue

                self.schedule.store_last_run(check_id, now)

                try:
                    self.execute_check(check)
                finally:
                    # reschedule under all circumstances, do not want to loose tasks
                    new_entry = (self.schedule.get_next_time(check.id, check.interval), check.id)

                    if check.id == 7:
                        self.logger.info("check 7 delta: %s next: %s", now - exec_time, new_entry[0] - now)

                    heapq.heappush(self.heap, new_entry)

    def run(self):
        self.update_checks_thread.start()
        self.update_alerts_thread.start()
        self.update_metrics_thread.start()
        self.update_captures_thread.start()
        self.update_properties_thread.start()

        trial_run = Subscriber(cherrypy.config, self._schedule_trial_runs, self.TRIAL_RUN_PUBSUB,
                               self.TRIAL_RUN_EXCHANGE)
        downtime_schedule = Subscriber(cherrypy.config, self._schedule_downtime, self.DOWNTIME_SCHEDULE_PUBSUB,
                                       self.DOWNTIME_SCHEDULE_EXCHANGE)
        downtime_remove = Subscriber(cherrypy.config, self._remove_downtime, self.DOWNTIME_REMOVE_PUBSUB,
                                     self.DOWNTIME_REMOVE_EXCHANGE)
        instant_evaluation = Subscriber(cherrypy.config, self._force_check_eval, self.INSTANT_EVAL_PUBSUB,
                                        self.INSTANT_EVAL_EXCHANGE)

        N_check_def_loop = 1
        check_def_loop_last_logged = time.time()

        if self.run_using_heap:
            trial_run.check_status()
            downtime_schedule.check_status()
            downtime_remove.check_status()
            instant_evaluation.check_status()

            self.run_heap_scheduler()
            self.schedule.save()
            sys.exit()

        last_exec_7 = 0
        while True:
            loop_scheduled = 0

            # Usually, the scheduler is deployed before the controller, so the first attempt to get check definitions
            # fails. The check definitions are eventually loaded by update method, but we need them to create the
            # schedule, hence the condition below.
            if self.check_definitions and not self.schedule.loaded:
                self.schedule.load(self.check_definitions)

            trial_run.check_status()
            downtime_schedule.check_status()
            downtime_remove.check_status()
            instant_evaluation.check_status()

            for each in self.check_definitions.values():

                if self.instance_code in ['3422', '3423']:
                    if self.instance_code == '3423' and each.interval > 30:
                        continue
                    elif self.instance_code == '3422' and each.interval <= 30:
                        continue
                    else:
                        pass

                interval = int(each.interval)
                expires = 2 * interval
                queue, routing_key = self.get_queue_and_routing_key(each)

                if self.schedule.is_scheduled(each.id, interval):

                    if each.id == 7:
                        _now = time.time()
                        self.logger.info("check 7 - last exec delta: %s", _now - last_exec_7 - 5)
                        last_exec_7 = _now

                    number_of_requests = 0
                    for entity in self._generate_check_entities(each, False):
                        req = {
                            'command': each.command,
                            'entity': entity,
                            'check_id': each.id,
                            'check_name': each.name,
                            'interval': interval,
                            'schedule_time': time.time(),
                        }

                        options = {
                            'soft_time_limit': min(interval, 60 * 7),
                            'time_limit': min(interval, 60 * 7) + 30,
                            'expires': expires,
                            'queue': queue,
                            'routing_key': routing_key,
                        }

                        #if str(each.id) in ['7', '285']:
                        #    self.logger.info('Sending check_id: %s => through queue: %s', each.id, queue)

                        # update count_checks_per_queue
                        self._add_to_count_checks(routing_key, 1)


                        try:
                            number_of_requests += 1

                            task = self.app.signature('check_and_notify', args=(req, self._generate_alerts(entity,
                                                      each.id)), options=options)
                            task.apply_async(task_id='check-{}-{}-{:.2f}'.format(each.id, entity['id'], time.time()))
                        except Exception, e:
                            self.logger.exception(e)

                    loop_scheduled += number_of_requests

                    if not number_of_requests:
                        if each.id in self.check_alert_map:

                            # remove entities from redis for that check and alerts,
                            # otherwise user gets no feedback about wrong entity filter

                            p = self.redis_connection.pipeline()
                            p.delete('zmon:checks:{}'.format(each.id))
                            for alert_id in list(self.check_alert_map[each.id]):
                                p.delete('zmon:alerts:{}:entities'.format(alert_id))

                            p.execute()

                            self.logger.info('No matching entities for check: %s id %s', each.name, each.id)
                        else:
                            self.logger.debug('No alerts defined for check: %s id %s', each.name, each.id)

                # periodically log aggregated info: count_checks_per_queue
                self._periodical_log_count_checks()

            # periodically report the time it takes to traverse the check_definitions loop
            cur_time = time.time()
            if cur_time - check_def_loop_last_logged >= self.LOG_COUNT_CHECK_INTERVAL:
                self.logger.info('Loop through all %d check_defs took: %.2f seconds, as average in %d cycles',
                                 len(self.check_definitions), (cur_time - check_def_loop_last_logged)
                                 / N_check_def_loop, N_check_def_loop)
                N_check_def_loop = 1
                check_def_loop_last_logged = cur_time
            else:
                N_check_def_loop += 1

            if not self.instance_code == '3423' and self.schedule.is_scheduled('cleanup',
                    self.DEFAULT_CLEANUP_INTERVAL):
                t = Thread(target=self._run_cleanup, name='initiate_cleanup')
                t.start()

            try:
                # write metrics into worker list :)
                p = self.redis_connection.pipeline()
                scheduler_name = 's-p{}.{}'.format(self.instance_code, self.host)
                p.sadd('zmon:metrics', scheduler_name)
                p.incrby('zmon:metrics:{}:{}'.format(scheduler_name, 'checks.count'), loop_scheduled)
                p.set('zmon:metrics:{}:ts'.format(scheduler_name), time.time())
                p.execute()
            except Exception:
                self.logger.exception('Error write metrics into worker list. Exception: ')

            # Check if parent process is still alive.
            if os.getppid() != self.parentPID:
                tasks_count = self.app.control.purge()
                self.logger.info('Stopping scheduler, discarding %s tasks', tasks_count)
                # Close pubsub channels.
                trial_run.unsubscribe()
                downtime_schedule.unsubscribe()
                downtime_remove.unsubscribe()
                instant_evaluation.unsubscribe()
                # Save current schedule to file.
                self.schedule.save()
                sys.exit()
            else:
                pass


def main():
    delete_suds_cache(SUDS_CACHE_DIR)

    cherrypy.config.update('/app/web.conf')

    #configuring redis connection handler
    RedisConnHandler.configure(**dict(cherrypy.config))

    app = Celery('zmon')
    app.conf.update(CELERY_TASK_SERIALIZER='json', CELERY_ACCEPT_CONTENT=['json'],
                    BROKER_URL=cherrypy.config.get('broker'), CELERY_QUEUES=(Queue('zmon:queue:default',
                    routing_key='default'), Queue('zmon:queue:internal', routing_key='internal'),
                    Queue('zmon:queue:secure', routing_key='secure'), Queue('zmon:queue:snmp', routing_key='snmp')),
                    CELERY_DEFAULT_EXCHANGE='zmon', CELERY_DEFAULT_ROUTING_KEY='default',
                    CELERY_DEFAULT_QUEUE='zmon:queue:default')

    loglevel = (logging.getLevelName(cherrypy.config['loglevel']) if 'loglevel' in cherrypy.config else logging.INFO)
    scheduler = ZmonScheduler(os.getpid(), app, '9999', socket.gethostname(), loglevel=loglevel)
    scheduler.start()


if __name__ == '__main__':
    main()
