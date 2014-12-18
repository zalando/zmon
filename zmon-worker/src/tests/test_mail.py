#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import patch, Mock, ANY

import datetime
import jinja2
import zmon_worker.notifications.mail as m
import smtplib
import unittest


class TestMail(unittest.TestCase):

    def setUp(self):
        m.Mail._config = {
            'notifications.mail.host': 'test_host',
            'notifications.mail.port': 25,
            'notifications.mail.sender': 'test_sender',
            'notifications.mail.on': True,
        }

    @patch.object(smtplib, 'SMTP')
    @patch.object(m, 'jinja_env')
    def test_send(self, mock_jinja, mock_smtp):
        alert = {
            'id': 'a1',
            'period': '',
            'name': 'test_alert',
            'notifications': ['send_sms("42", repeat=5)', 'send_mail("test@example.org", repeat=5)'],
            'check_id': 1,
            'entity': {'id': 'e1'},
        }
        s = Mock()
        mock_smtp.return_value = s

        # Regular send
        repeat = m.Mail.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, 'test@example.org')
        self.assertEqual(0, repeat)
        mock_jinja.get_template.assert_called_with('alert.txt')
        mock_smtp.assert_called_with('test_host', 25)
        s.sendmail.assert_called_with('test_sender', ['test@example.org'], ANY)

        # Send with repeat in HTML
        repeat = m.Mail.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, 'test@example.org', repeat=100, html=True)
        self.assertEqual(100, repeat)
        mock_jinja.get_template.assert_called_with('alert.html')
        mock_smtp.assert_called_with('test_host', 25)
        s.sendmail.assert_called_with('test_sender', ['test@example.org'], ANY)

        # Exception handling 1: Jinja Error
        mock_smtp.reset_mock()
        s.reset_mock()
        mock_smtp.return_value = s
        mock_jinja.reset_mock()
        t = Mock()
        t.render.side_effect = jinja2.TemplateError('Jinja Error')
        mock_jinja.get_template.return_value = t

        repeat = m.Mail.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, 'test@example.org', repeat=101)
        self.assertEqual(101, repeat)
        mock_jinja.get_template.assert_called_with('alert.txt')
        self.assertFalse(mock_smtp.called)

        # Exception handling 2: SMTP Error
        mock_jinja.reset_mock()
        t = Mock()
        t.render.return_value = 'test'
        mock_jinja.get_template.return_value = t
        mock_smtp.reset_mock()
        s = Mock()
        s.sendmail.side_effect = Exception('Error connecting to host')
        mock_smtp.return_value = s

        repeat = m.Mail.send({
            'captures': {},
            'changed': True,
            'value': {'value': 1.0},
            'entity': {'id': 'e1'},
            'is_alert': True,
            'alert_def': alert,
            'duration': datetime.timedelta(seconds=0),
        }, 'test@example.org', repeat=102)
        self.assertEqual(102, repeat)
        mock_jinja.get_template.assert_called_with('alert.txt')
        self.assertTrue(mock_smtp.called)


if __name__ == '__main__':
    unittest.main()
