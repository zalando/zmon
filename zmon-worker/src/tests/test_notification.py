#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from notifications.notification import BaseNotification


class TestBaseNotification(unittest.TestCase):

    def test_get_subject_success(self):
        alert = {'name': '{thing} is {status}'}
        captures = {'thing': 'everything', 'status': 'broken'}
        entity = {'id': 'everything'}
        ctx = {
            'is_alert': True,
            'changed': True,
            'alert_def': alert,
            'captures': captures,
            'entity': entity,
        }
        self.assertEquals(BaseNotification._get_subject(ctx), 'NEW ALERT: everything is broken on everything')

    def test_get_subject_with_bad_capture(self):
        alert = {'name': '{thingy} is {result}'}
        captures = {'thing': 'everything', 'status': 'broken'}
        entity = {'id': 'everything'}
        ctx = {
            'is_alert': True,
            'changed': True,
            'alert_def': alert,
            'captures': captures,
            'entity': entity,
        }
        self.assertEquals(BaseNotification._get_subject(ctx), 'NEW ALERT: {thingy} is {result} on everything')

    def test_get_subject_with_bad_formatting(self):
        alert = {'name': '{thing:w} is {status}'}
        captures = {'thing': 'everything', 'status': 'broken'}
        entity = {'id': 'everything'}
        ctx = {
            'is_alert': True,
            'changed': True,
            'alert_def': alert,
            'captures': captures,
            'entity': entity,
        }
        self.assertEquals(BaseNotification._get_subject(ctx),
                          "NEW ALERT: <<< Unformattable name '{thing:w} is {status}': "
                          + "Unknown format code 'w' for object of type 'str' >>> on everything")


