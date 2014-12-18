#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import eventlog
import json
import logging
import time
import unittest

from mock import call, patch, Mock, ANY
from tasks import notify


def make_mock_evaluate_alert(is_alert, captures):

    def evaluate_alert(self, alert_def, req, result):
        return is_alert, captures

    return evaluate_alert


class TestTasks(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('zmon.test_tasks')
        logger.setLevel(logging.CRITICAL)
        self.mock = Mock()
        self.mock.worker_name = 'p0000.localhost'
        self.mock._captures_local = []

    def tearDown(self):
        self.mock.reset_mock()

    @patch.object(notify, '_log_event')
    @patch.object(notify, '_evaluate_downtimes', lambda *args: [])
    def test_notify(self, mock_log_event):

        check_result = {'ts': time.time(), 'td': time.time() + 5, 'value': 5}

        # Simple, happy path, single alert should create one entry in redis and return one alert id.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            alert = {
                'id': 'a1',
                'period': '',
                'notifications': [],
                'check_id': 1,
            }
            result = notify.notify(self.mock, check_result, {'entity': {'id': 'e1'}, 'check_name': 'test_check',
                                   'check_id': 'whatever'}, [alert])

            self.mock.con.hset.assert_called_once_with('zmon:alerts:a1:entities', 'e1', '{}')
            self.assertIn('a1', result)
            mock_log_event.assert_has_calls([call('ALERT_STARTED', alert, check_result), call('ALERT_ENTITY_STARTED',
                                            alert, check_result, 'e1')])

        self.mock.reset_mock()

        # Simple path with single time period which is active, should create one entry and return one id.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch('timeperiod.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.datetime(2014, 2, 11, 14, 30)
                self.mock.con.get.return_value = '{"start_time": 1395067678}'
                # This means that the alert changed state from inactive to active.
                self.mock.con.sadd.return_value = 1
                alert = {
                    'id': 'a2',
                    'period': 'hr {9-17}',
                    'notifications': [],
                    'check_id': 1,
                }
                result = notify.notify(self.mock, check_result, {'entity': {'id': 'e2'}, 'check_name': 'test_check',
                                       'check_id': 'whatever'}, [alert])

                self.mock.con.hset.assert_called_once_with('zmon:alerts:a2:entities', 'e2', '{}')
                self.assertIn('a2', result)
                mock_log_event.assert_has_calls([call('ALERT_STARTED', alert, check_result), call('ALERT_ENTITY_STARTED'
                                                , alert, check_result, 'e2')])

        self.mock.reset_mock()
        mock_log_event.reset_mock()

        # Single time period, inactive, shouldn't create or return anything, but should cleanup active alert.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch('timeperiod.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.datetime(2014, 2, 11, 14, 30)

                pipeline = Mock()
                pipeline.srem.return_value = True
                pipeline.delete.return_value = True
                self.mock.con.pipeline.return_value = pipeline
                self.mock.con.smembers.return_value = set(['e3'])
                self.mock.con.sadd.return_value = 0

                result = notify.notify(self.mock, check_result, {'entity': {'id': 'e3'}, 'check_name': 'test_check',
                                       'check_id': 'whatever'}, [{
                    'id': 'a3',
                    'period': 'hr {0-8}',
                    'notifications': [],
                    'check_id': 1,
                }])

                sadd_calls = [call('zmon:alerts:a3', 'e3'), call('zmon:alerts', 'a3')]

                self.assertListEqual(self.mock.con.sadd.call_args_list, sadd_calls)
                self.assertNotIn('a3', result)
                self.assertListEqual([call('zmon:alerts:a3', 'e3'), call('zmon:alerts', 'a3')],
                                     pipeline.srem.call_args_list)
                self.assertListEqual([call('zmon:alerts:a3:e3'), call('zmon:notifications:a3:e3')],
                                     pipeline.delete.call_args_list)
                self.assertFalse(mock_log_event.called)

        self.mock.reset_mock()

        # Two alert definitions, one with time period, one without, both active. Should return one alert id and cleanup
        # after the other.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch('timeperiod.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.datetime(2014, 2, 11, 14, 30)

                pipeline = Mock()
                pipeline.srem.return_value = True
                pipeline.delete.return_value = True
                self.mock.con.pipeline.return_value = pipeline
                self.mock.con.smembers.return_value = set(['e3', 'e4'])

                result = notify.notify(self.mock, check_result, {'entity': {'id': 'e4'}, 'check_name': 'test_check',
                                       'check_id': 'whatever'}, [{
                    'id': 'a4',
                    'period': 'hr {0-8}',
                    'notifications': [],
                    'check_id': 1,
                }, {
                    'id': 'a5',
                    'period': '',
                    'notifications': [],
                    'check_id': 1,
                }])

                self.assertListEqual([call('zmon:alerts:a4:entities', 'e4', '{}'), call('zmon:alerts:a5:entities', 'e4'
                                     , '{}')], self.mock.con.hset.call_args_list)

                self.assertIn('a5', result)
                self.assertNotIn('a4', result)

                self.assertListEqual([call('zmon:alerts:a4', 'e4')], pipeline.srem.call_args_list)
                self.assertListEqual([call('zmon:alerts:a4:e4'), call('zmon:notifications:a4:e4')],
                                     pipeline.delete.call_args_list)
                # In this case event shouldn't be logged because none of the alerts changed its state.
                self.assertFalse(mock_log_event.called)

    def test_evaluate_alert(self):
        alert_def = {'id': 'alert_id', 'check_id': '1', 'condition': '!=0'}
        check_request = {'id': '1', 'entity': {'id': 'entity_id'}}

        result = {'value': 1.0}

        # PF-3175 Result of alert evaluation should always be boolean.
        with patch.object(notify, 'evaluate_condition', return_value=42.0):
            with patch.object(eventlog, 'log', return_value=None):
                with patch.object(notify, '_evaluate_downtimes', return_value=[]):
                    is_alert, captures = notify.evaluate_alert(Mock(), alert_def, check_request, result)
                    self.assertIsInstance(is_alert, bool)

    def test_force_alert(self):
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch.object(notify, '_log_event', return_value=True):
                with patch.object(notify, '_evaluate_downtimes', return_value=[]):
                    result = notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                           'check_id': 'whatever'}, [{
                        'id': 'a1',
                        'period': '',
                        'notifications': [],
                        'check_id': 1,
                    }], force_alert=True)

                    self.assertFalse(notify.evaluate_alert.called)
                    self.assertIn('a1', result)

    @patch.object(notify, '_log_event', lambda *args: True)
    @patch.object(notify, '_evaluate_downtimes', lambda *args: [])
    def test_repeat_notification(self):
        alert = {
            'id': 'a1',
            'period': '',
            'notifications': ['send_sms("42", repeat=5)', 'send_mail("test@example.org", repeat=5)'],
            'check_id': 1,
        }

        # First notification should send the email and set the timestamp in redis.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch.object(notify.Mail, 'send', return_value=5):
                with patch.object(notify.Sms, 'send', return_value=5):
                    with patch.object(time, 'time') as mock_time:
                        mock_time.return_value = 5
                        self.mock.con.hset.return_value = True
                        self.mock.con.sadd.return_value = 1
                        notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                      'check_id': 'whatever'}, [alert])

                        notify.Mail.send.assert_called_once_with({
                            'captures': {},
                            'changed': True,
                            'value': {'value': 1.0},
                            'entity': {'id': 'e1'},
                            'is_alert': True,
                            'alert_def': alert,
                            'duration': datetime.timedelta(seconds=0),
                        }, 'test@example.org', repeat=5)

                        notify.Sms.send.assert_called_once_with({
                            'captures': {},
                            'changed': True,
                            'value': {'value': 1.0},
                            'entity': {'id': 'e1'},
                            'is_alert': True,
                            'alert_def': alert,
                            'duration': datetime.timedelta(seconds=0),
                        }, '42', repeat=5)

                        calls = [call('zmon:notifications:a1:e1', 'send_sms("42", repeat=5)', 10),
                                 call('zmon:notifications:a1:e1', 'send_mail("test@example.org", repeat=5)', 10)]
                        self.mock.con.hset.assert_has_calls(calls)

        # Too soon, nothing should be sent, nor added to redis.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch.object(notify.Mail, 'send', return_value=5):
                with patch.object(notify.Sms, 'send', return_value=5):
                    with patch.object(time, 'time') as mock_time:
                        mock_time.return_value = 7
                        self.mock.con.get.return_value = '{"start_time": 5}'
                        self.mock.con.hgetall.return_value = {'send_sms("42", repeat=5)': '10',
                                'send_mail("test@example.org", repeat=5)': '10'}
                        self.mock.con.sadd.return_value = 0
                        notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                      'check_id': 'whatever'}, [alert])

                        self.assertFalse(notify.Sms.send.called)
                        self.assertFalse(notify.Mail.send.called)

        # Repeating notification, should be sent and set a timestamp in redis.
        with patch.object(notify, 'evaluate_alert', return_value=(True, {})):
            with patch.object(notify.Mail, 'send', return_value=5):
                with patch.object(notify.Sms, 'send', return_value=5):
                    with patch.object(time, 'time') as mock_time:
                        mock_time.return_value = 11
                        self.mock.con.get.return_value = '{"start_time": 5}'
                        self.mock.con.hgetall.return_value = {'send_sms("42", repeat=5)': '10',
                                'send_mail("test@example.org", repeat=5)': '10'}
                        self.mock.con.sadd.return_value = 0
                        notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                      'check_id': 'whatever'}, [alert])

                        notify.Mail.send.assert_called_once_with({
                            'captures': {},
                            'changed': False,
                            'value': {'value': 1.0},
                            'entity': {'id': 'e1'},
                            'is_alert': True,
                            'alert_def': alert,
                            'duration': datetime.timedelta(seconds=11 - 5),
                        }, 'test@example.org', repeat=5)

                        notify.Sms.send.assert_called_once_with({
                            'captures': {},
                            'changed': False,
                            'value': {'value': 1.0},
                            'entity': {'id': 'e1'},
                            'is_alert': True,
                            'alert_def': alert,
                            'duration': datetime.timedelta(seconds=11 - 5),
                        }, '42', repeat=5)

                        calls = [call('zmon:notifications:a1:e1', 'send_sms("42", repeat=5)', 16),
                                 call('zmon:notifications:a1:e1', 'send_mail("test@example.org", repeat=5)', 16)]
                        self.mock.con.hset.assert_has_calls(calls)

        # End of alert, notification should be sent, repeating should stop
        with patch.object(notify, 'evaluate_alert', return_value=(False, {})):
            with patch.object(notify.Mail, 'send', return_value=5):
                with patch.object(notify.Sms, 'send', return_value=5):
                    self.mock.con.delete.return_value = True
                    self.mock.con.hdel.return_value = True
                    self.mock.con.srem.return_value = 1
                    notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                  'check_id': 'whatever'}, [alert])

                    notify.Mail.send.assert_called_once_with({
                        'captures': {},
                        'changed': True,
                        'value': {'value': 1.0},
                        'entity': {'id': 'e1'},
                        'is_alert': False,
                        'alert_def': alert,
                        'duration': datetime.timedelta(0),
                    }, 'test@example.org', repeat=5)

                    notify.Sms.send.assert_called_once_with({
                        'captures': {},
                        'changed': True,
                        'value': {'value': 1.0},
                        'entity': {'id': 'e1'},
                        'is_alert': False,
                        'alert_def': alert,
                        'duration': datetime.timedelta(0),
                    }, '42', repeat=5)

                    self.assertListEqual([call('zmon:alerts:a1:e1'), call('zmon:notifications:a1:e1')],
                                         self.mock.con.delete.call_args_list)

    @patch.object(notify, '_log_event', lambda *args: True)
    @patch.object(notify, '_evaluate_downtimes', lambda *args: [])
    def test_exception_handling(self):
        # PF-3318 Handling malformed time periods
        alerts = [{
            'id': 'a1',
            'period': 'hr {9-1q}',
            'notifications': [],
            'check_id': 1,
        }, {
            'id': 'a2',
            'period': '',
            'notifications': [],
            'check_id': 1,
        }]

        req = {'entity': {'id': 'e1'}, 'check_name': 'test_check', 'check_id': 'whatever'}

        with patch.object(notify, 'evaluate_alert', lambda *args: (True, {})):
            result = notify.notify(self.mock, {'value': 1.0}, req, alerts)

        self.assertIsNotNone(result)
        self.assertListEqual(['a1', 'a2'], result)
        self.mock.logger.warn.assert_called_once_with(ANY, 'a1')
        # First alert
        captures = json.loads(self.mock.con.hset.call_args_list[0][0][2])
        result = json.loads(self.mock.con.set.call_args_list[0][0][1])
        self.assertIn('exception', captures)
        self.assertIn('exception', result['captures'])
        # Second alert
        captures = json.loads(self.mock.con.hset.call_args_list[1][0][2])
        result = json.loads(self.mock.con.set.call_args_list[1][0][1])
        self.assertNotIn('exception', captures)
        self.assertNotIn('exception', result['captures'])

        # PF-3378 Handling malformed JSON
        alert = [{
            'id': 'a3',
            'period': '',
            'notifications': [],
            'check_id': 1,
        }]

        with patch.object(notify, 'evaluate_alert', lambda *args: (True, {})):
            self.mock.con.get.return_value = '{"This is not valid JSON...'
            result = notify.notify(self.mock, {'value': 1.0}, req, alert)

        self.assertIsNotNone(result)
        self.assertIn('a3', result)

    @patch.object(notify, '_log_event', lambda *args: True)
    @patch.object(notify, '_evaluate_downtimes', lambda *args: [])
    def test_storing_captures(self):
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 1
            self.mock._captures_local = []
            self.mock.worker_name = 'p0.host'
            result = notify.notify(self.mock, {'value': 1.0}, {'entity': {'id': 'e1'}, 'check_name': 't',
                                   'check_id': 'whatever'}, [{
                'id': 'a1',
                'condition': 'capture(test=value) > 0',
                'period': '',
                'notifications': [],
                'check_id': 1,
            }])

        self.assertIn('a1', result)
        assert self.mock._captures_local == [('p0_host.alerts.a1.e1.captures.test', 1.0, 1)]


if __name__ == '__main__':
    unittest.main()
