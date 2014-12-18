#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest

from mock import patch, ANY, Mock

from tasks import notify
from tasks import trial_run
from tasks.zmontask import ZmonTask, manifest


class TestTrialRun(unittest.TestCase):

    def setUp(self):
        manifest.instance = 'local'

    @patch.object(ZmonTask, '_wsdlurl', 'whatever', create=True)
    def test(self):
        req = {
            'name': 'TR:whatever',
            'command': '1000',
            'interval': 60,
            'entity': {'id': '123', 'type': 'city'},
        }

        alerts = [{
            'id': 'TR:whatever',
            'check_id': 'TR:whatever',
            'condition': '==1000',
            'period': '',
        }]
        request = Mock()
        request.timelimit = [None, 5]

        with patch.object(ZmonTask, 'con', create=True) as redis_connection_mock:
            with patch.object(ZmonTask, 'request', request):
                trial_run(req, alerts)

        self.assertEquals(redis_connection_mock.hset.call_args[0][0], 'zmon:trial_run:whatever:results')
        self.assertEquals(redis_connection_mock.hset.call_args[0][1], '123')
        result = json.loads(redis_connection_mock.hset.call_args[0][2])
        self.assertEquals(result['captures'], {})
        self.assertEquals(result['in_period'], 1)
        self.assertEquals(result['is_alert'], True)
        self.assertEquals(result['value']['value'], 1000)
        self.assertEquals(result['entity'], {'id': '123', 'type': 'city'})

        redis_connection_mock.expire.assert_called_with('zmon:trial_run:whatever:results', ANY)

        alerts = [{
            'id': 'TR:period',
            'check_id': 'TR:period',
            'condition': '==1000',
            'period': 'hr {7-1q}',
        }]

        with patch.object(ZmonTask, 'con', create=True) as redis_connection_mock:
            with patch.object(ZmonTask, 'request', request):
                trial_run(req, alerts)

        self.assertEquals(redis_connection_mock.hset.call_args[0][0], 'zmon:trial_run:period:results')
        self.assertEquals(redis_connection_mock.hset.call_args[0][1], '123')
        result = json.loads(redis_connection_mock.hset.call_args[0][2])
        self.assertIn('exception', result['captures'])
        self.assertEquals(result['in_period'], 1)

    def test_exception_handling(self):
        return_values = [TypeError('Something is not JSON serializable'), 'response']

        # To mock different behaviour on subsequent calls, we need to change side effect's return value. When it's
        # called for the second time, we return the argument it was called with which is a dict with trial run results.
        def side_effect(*args, **kwargs):
            result = return_values.pop(0)
            if isinstance(result, Exception):
                raise result
            return args[0]

        mock = Mock()
        req = {'name': 'TR:exception', 'command': '1000', 'entity': {'id': '123', 'type': 'city'}}

        alerts = [{
            'id': 'TR:exception',
            'check_id': 'TR:exception',
            'condition': '==1000',
            'period': '',
        }]

        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch.object(json, 'dumps', side_effect=side_effect):
                result = notify.notify_for_trial_run(mock, {'value': 1000, 'ts': 1, 'td': 1}, req, alerts)

        self.assertIn('TR:exception', result)
        self.assertDictEqual({
            'entity': {'id': '123', 'type': 'city'},
            'value': 'Something is not JSON serializable',
            'captures': {},
            'is_alert': True,
            'in_period': True,
        }, mock.con.hset.call_args_list[0][0][2])


if __name__ == '__main__':
    unittest.main()
