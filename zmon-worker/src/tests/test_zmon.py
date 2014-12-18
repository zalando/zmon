#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import Mock, patch, PropertyMock

import datetime
import json
import zmon_worker.functions.zmon as zmon
import time
import unittest


class CheckDefinition(object):

    def __init__(self, c_id, interval):
        self.id = c_id
        self.interval = interval


class AlertDefinition(object):

    def __init__(self, a_id, team, responsible_team, check_id, period):
        self.id = a_id
        self.team = team
        self.responsibleTeam = responsible_team
        self.checkDefinitionId = check_id
        self.period = period


def make_pipeline_execute_mock(calls):

    def mock_pipeline_execute():
        return calls.pop()

    return mock_pipeline_execute


class ZmonWrapperTests(unittest.TestCase):

    @patch.object(zmon, 'redis', new_callable=Mock)
    @patch.object(zmon, 'Client', new_callable=Mock)
    def test_stale_alerts(self, mock_wsdl_client, mock_redis):
        mock_calls = Mock()
        # 1. Active alert with active check and up-to-date results, no time period.
        # 2. Active alert with active check and outdated results because of time period.
        # 3. Active alert with active check and up-to-date results, but the check only runs daily.
        # 4. Active alert with inactive check. (STALE)
        # 5. Active alert with active check, without time period, but with outdated results. (STALE)
        # 6. Active alert with active check, without time period, but the check doesn't match any entities, so it
        # produces no results (STALE)
        # 7. Active alert with active check, without time period, check throws an exception, results are stored, but
        # 'notify' is triggered with the exception, evaluates captures and stored keys in redis.
        mock_calls.getAllActiveAlertDefinitions.return_value = 0, [
            AlertDefinition(1, 'team1', 'team2', 1, ''),
            AlertDefinition(2, 'team1', 'team2', 2, 'hr{9-17}'),
            AlertDefinition(3, 'team1', 'team2', 3, ''),
            AlertDefinition(4, 'team1', 'team2', 4, ''),
            AlertDefinition(5, 'team1', 'team2', 5, ''),
            AlertDefinition(6, 'team1', 'team2', 6, ''),
            AlertDefinition(7, 'team1', 'team2', 7, ''),
        ]
        mock_calls.getAllActiveCheckDefinitions.return_value = 0, [
            CheckDefinition(1, 60),
            CheckDefinition(2, 40),
            CheckDefinition(3, 60 * 60 * 24),
            CheckDefinition(5, 1),
            CheckDefinition(6, 120),
            CheckDefinition(7, 60),
        ]
        mock_service = PropertyMock(return_value=mock_calls)
        service_mock = Mock()
        type(service_mock).service = mock_service
        mock_wsdl_client.return_value = service_mock

        mock_client = Mock()
        mock_pipeline = Mock()
        mock_pipeline.execute = make_pipeline_execute_mock([[
            json.dumps({'value': 1, 'ts': 55, 'td': 1}),
            json.dumps({'value': 1, 'ts': 1, 'td': 1}),
            json.dumps({'value': 1, 'ts': 1, 'td': 1}),
            json.dumps({'value': 1, 'ts': 1, 'td': 1}),
            json.dumps({'value': 1, 'ts': 1, 'td': 1}),
            None,
            json.dumps({'value': 'Exception', 'ts': 1, 'td': 1}),
        ], [
            ['e1'],
            ['e2', 'e3'],
            ['e4'],
            ['e5'],
            ['e7'],
        ]])
        mock_client.keys.return_value = [
            'zmon:alerts:1:entities',
            'zmon:alerts:2:entities',
            'zmon:alerts:3:entities',
            'zmon:alerts:5:entities',
            'zmon:alerts:7:entities',
        ]
        mock_client.pipeline.return_value = mock_pipeline
        mock_redis.StrictRedis.return_value = mock_client

        with patch.object(time, 'time') as mock_time:
            with patch('timeperiod.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.datetime(2014, 5, 16, 8, 30)
                mock_time.return_value = 305
                z = zmon.ZmonWrapper('wsdl_url', 'redis_host', 6379)
                inactive_alerts = z.stale_active_alerts()

        self.assertEquals(len(inactive_alerts), 3)
        self.assertEquals(inactive_alerts[0]['id'], 4)
        self.assertEquals(inactive_alerts[1]['id'], 5)
        self.assertEquals(inactive_alerts[2]['id'], 6)

    @patch.object(zmon, 'redis', new_callable=Mock)
    @patch.object(zmon, 'Client', new_callable=Mock)
    def test_stale_total(self, mock_wsdl_client, mock_redis):
        mock_calls = Mock()
        mock_calls.getAllActiveAlertDefinitions.return_value = 0, [AlertDefinition(1, 'team1', 'team2', 1, '')]
        mock_calls.getAllActiveCheckDefinitions.return_value = 0, [CheckDefinition(1, 60)]
        mock_service = PropertyMock(return_value=mock_calls)
        service_mock = Mock()
        type(service_mock).service = mock_service
        mock_wsdl_client.return_value = service_mock

        mock_client = Mock()
        mock_pipeline = Mock()
        mock_pipeline.execute = make_pipeline_execute_mock([[['e1'], ['e2', 'e3'], ['e4'], ['e5']]])
        mock_client.keys.return_value = ['zmon:alerts:1:entities', 'zmon:alerts:2:entities', 'zmon:alerts:3:entities',
                                         'zmon:alerts:5:entities']
        mock_client.pipeline.return_value = mock_pipeline
        mock_redis.StrictRedis.return_value = mock_client

        z = zmon.ZmonWrapper('wsdl_url', 'redis_host', 6379)
        entities_count = z.check_entities_total()

        self.assertEquals(entities_count, 5)


if __name__ == '__main__':
    unittest.main()
