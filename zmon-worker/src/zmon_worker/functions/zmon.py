#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from zmon_worker.errors import CheckError
from functools import partial
from suds.client import Client
from time_ import parse_timedelta
from timeperiod import in_period, InvalidFormat
from zmon_worker.common.utils import async_memory_cache

import sys
import json
import redis
import time

logger = logging.getLogger(__name__)

CHECK_REFRESH_TIME = 240
ALERT_REFRESH_TIME = 120


class ZmonWrapper(object):

    ZMON_ALERTS_ENTITIES_PATTERN = 'zmon:alerts:*:entities'

    def __init__(self, wsdl, host, port):
        try:
            self.__ws_client = Client(url=wsdl)
            self.__ws_client.set_options(cache=None)
        except Exception:
            raise CheckError('ZmonWrapper Error: failed to connect to zmon-controller')

        self.__redis = redis.StrictRedis(host, port)
        self.__checks = {}
        self.__alerts = []

        self.logger = logger

        self.__checks = self.__load_check_definitions()
        self.__alerts = self.__load_alert_definitions()

    @async_memory_cache.cache_on_arguments(namespace='zmon-worker', expiration_time=ALERT_REFRESH_TIME)
    def __load_alert_definitions(self):
        try:
            response = self.__ws_client.service.getAllActiveAlertDefinitions()
        except Exception:
            self.logger.exception('ZmonWrapper Error: failed to load alert definitions')
            raise CheckError('ZmonWrapper Error: failed to load alert definitions'), None, sys.exc_info()[2]
        else:
            return [{
                'id': a.id,
                'team': a.team,
                'responsible_team': a.responsibleTeam,
                'check_id': a.checkDefinitionId,
                'period': (a.period or '' if hasattr(a, 'period') else ''),
            } for a in response[1]]

    @async_memory_cache.cache_on_arguments(namespace='zmon-worker', expiration_time=CHECK_REFRESH_TIME)
    def __load_check_definitions(self):
        try:
            response = self.__ws_client.service.getAllActiveCheckDefinitions()
        except Exception:
            self.logger.exception('ZmonWrapper Error: failed to load check definitions')
            raise CheckError('ZmonWrapper Error: failed to load check definitions'), None, sys.exc_info()[2]
        else:
            return dict((c.id, {'interval': c.interval}) for c in response[1])

    @staticmethod
    def _is_entity_alert_stale(last_run, period):
        '''
        Checks whether check's last run is within given period.

        >>> ZmonWrapper._is_entity_alert_stale(None, 60)
        False
        >>> ZmonWrapper._is_entity_alert_stale(time.time(), 10)
        False
        >>> ZmonWrapper._is_entity_alert_stale(time.time() - 20, 10)
        True
        '''

        return (False if last_run is None else time.time() - last_run > period)

    def __is_alert_stale(self, alert, evaluated_alerts, check_results, multiplier, offset):
        a_id = alert['id']  # alert id
        c_id = alert['check_id']  # check id
        r_id = partial('{}:{}'.format, c_id)  # helper function used in iterator to generate result id

        try:
            is_in_period = in_period(alert.get('period', ''))
        except InvalidFormat:
            self.logger.warn('Alert with id %s has malformed time period.', a_id)
            is_in_period = True

        if is_in_period:
            return a_id not in evaluated_alerts or any(self._is_entity_alert_stale(check_results.get(r_id(entity)),
                                                       multiplier * self.__checks[c_id]['interval'] + offset)
                                                       for entity in evaluated_alerts[a_id])
        else:
            return False

    def stale_active_alerts(self, multiplier=2, offset='5m'):
        '''
        Returns a list of alerts that weren't executed in a given period of time. The period is calculated using
        multiplier and offset: check's interval * multiplier + offset.
        Parameters
        ----------
        multiplier: int
            Multiplier for check's interval.
        offset: str
            Time offset, for details see parse_timedelta function in zmon-worker/src/function/time_.py.
        Returns
        -------
        list
            A list of stale active alerts.
        '''

        alert_entities = self.__redis.keys(self.ZMON_ALERTS_ENTITIES_PATTERN)

        # Load evaluated alerts and their entities from redis.
        p = self.__redis.pipeline()
        for key in alert_entities:
            p.hkeys(key)
        entities = p.execute()
        evaluated_alerts = dict((int(key.split(':')[2]), entities[i]) for (i, key) in enumerate(alert_entities))

        # Load check results for previously loaded alerts and entities.
        check_ids = []
        for alert in self.__alerts:
            if alert['id'] in evaluated_alerts:
                for entity in evaluated_alerts[alert['id']]:
                    p.lindex('zmon:checks:{}:{}'.format(alert['check_id'], entity), 0)
                    check_ids.append('{}:{}'.format(alert['check_id'], entity))
        results = p.execute()
        check_results = dict((check_id, json.loads(results[i])['ts']) for (i, check_id) in enumerate(check_ids)
                             if results[i])

        return [{'id': alert['id'], 'team': alert['team'], 'responsible_team': alert['responsible_team']} for alert in
                self.__alerts if self.__is_alert_stale(alert, evaluated_alerts, check_results, multiplier,
                parse_timedelta(offset).total_seconds())]

    def check_entities_total(self):
        '''
        Returns total number of checked entities.
        '''

        alert_entities = self.__redis.keys(self.ZMON_ALERTS_ENTITIES_PATTERN)
        p = self.__redis.pipeline()
        for key in alert_entities:
            p.hkeys(key)
        entities = p.execute()

        return sum(len(e) for e in entities)

