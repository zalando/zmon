#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zmon_worker.notifications.sms import Sms
from mock import patch, Mock, PropertyMock

import datetime
import eventlog
import requests
import unittest


class TestSms(unittest.TestCase):

    def setUp(self):
        Sms._config = {
            'notifications.sms.provider_url': 'test_url',
            'notifications.sms.contact_groups': {},
            'notifications.sms.maxlength': 160,
            'notifications.sms.apikey': 'test_key',
            'notifications.sms.sender': 'test_sender',
            'notifications.sms.route': 'test_route',
            'notifications.sms.on': True,
        }

    @patch.object(eventlog, 'log')
    @patch.object(requests, 'get')
    def test_send(self, mock_requests, mock_eventlog):
        alert = {
            'id': 'a1',
            'period': '',
            'name': 'test_alert',
            'notifications': ['send_sms("42", repeat=5)', 'send_mail("test@example.org", repeat=5)'],
            'check_id': 1,
            'entity': {'id': 'e1'},
        }
        r = Mock()
        p = PropertyMock(return_value=100)
        type(r).status_code = p
        mock_requests.return_value = r

        # Regular send
        repeat = Sms.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, '42')
        mock_requests.assert_called_with('test_url', params={
            'to': '42',
            'key': 'test_key',
            'from': 'test_sender',
            'route': 'test_route',
            'message': 'NEW ALERT: test_alert on e1',
            'cost': 1,
            'message_id': 1,
        }, verify=False)
        self.assertEqual(0, repeat)
        mock_eventlog.assert_called_with(Sms._EVENTS['SMS_SENT'].id, alertId=alert['id'], entity=alert['entity']['id'],
                                         phoneNumber='42', httpStatus=100)

        # Send with repeat
        repeat = Sms.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, '42', repeat=300)
        mock_requests.assert_called_with('test_url', params={
            'to': '42',
            'key': 'test_key',
            'from': 'test_sender',
            'route': 'test_route',
            'message': 'NEW ALERT: test_alert on e1',
            'cost': 1,
            'message_id': 1,
        }, verify=False)
        self.assertEqual(300, repeat)
        mock_eventlog.assert_called_with(Sms._EVENTS['SMS_SENT'].id, alertId=alert['id'], entity=alert['entity']['id'],
                                         phoneNumber='42', httpStatus=100)

        # Exception handling
        mock_requests.reset_mock()
        mock_eventlog.reset_mock()
        r.raise_for_status.side_effect = requests.RequestException('test')
        mock_requests.return_value = r
        repeat = Sms.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, '42', repeat=100)
        self.assertEqual(100, repeat)
        self.assertFalse(mock_eventlog.called)


if __name__ == '__main__':
    unittest.main()
