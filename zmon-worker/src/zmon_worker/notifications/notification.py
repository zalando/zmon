#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging

class BaseNotification(object):

    _config = {}

    _EVENTS = None

    @classmethod
    def update_config(cls, new_config):
        cls._config.update(new_config)

    @classmethod
    def register_eventlog_events(cls, events):
        cls._EVENTS = events

    @classmethod
    def set_redis_con(cls, r):
        cls.__redis_conn = r

    @classmethod
    def _get_subject(cls, alert, custom_message=None):
        """
        >>> BaseNotification._get_subject({'is_alert': True, 'changed': True, 'alert_def':{'name': 'Test'}, 'entity':{'id':'hostxy'}, 'captures': {}})
        'NEW ALERT: Test on hostxy'

        >>> BaseNotification._get_subject({'is_alert': True, 'changed': False, 'alert_def':{'name': 'Test'}, 'entity':{'id':'hostxy'}, 'captures': {}, 'duration': datetime.timedelta(seconds=30)})
        'ALERT ONGOING: Test on hostxy for 0:00:30'
        """

        if alert['changed']:
            event = ('NEW ALERT' if alert and alert.get('is_alert') else 'ALERT ENDED')
        else:
            event = 'ALERT ONGOING'

        name = cls._get_expanded_alert_name(alert, custom_message)

        if not custom_message:
            return ('{}: {} on {} for {}'.format(event, name, alert['entity']['id'], str(alert['duration'
                    ])[:7]) if alert.get('duration') else '{}: {} on {}'.format(event, name, alert['entity']['id']))
        else:
            return '{}: {}'.format(event, name)

    @classmethod
    def _get_expanded_alert_name(cls, alert, custom_message=None):
        name = (alert['alert_def']['name'] if not custom_message else custom_message)
        try:
            replacements = {'entities': alert['entity']['id']}
            replacements.update(alert['captures'])
            return name.format(**replacements)
        except KeyError, e:
            return name  # This is fairly normal. Just use the unformatted name.
        except Exception, e:
            return "<<< Unformattable name '{name}': {message} >>>".format(name=name, message=e)

    @classmethod
    def send(cls, alert, *args, **kwargs):
        raise NotImplementedError('Method meant to be overriden by subclass')

    @classmethod
    def resolve_group(cls, targets, phone=False):
        new_targets = []
        for target in targets:
            prefix = target[0:target.find(':')+1]
            if not prefix in ['group:', 'active:']:
                new_targets.append(target)
                continue

            group_id = target[target.find(':')+1:]

            key = 'zmon:group:'+group_id + (':members' if prefix == 'group:' else ':active')
            team = cls.__redis_conn.smembers(key)

            if not team:
                logging.warn("no members found for group: %s", target)
                continue

            if not phone:
                new_targets.extend(team)
            else:
                for m in team:
                    phone_numbers = cls.__redis_conn.smembers('zmon:member:'+m+':phone')
                    new_targets.extend(phone_numbers)

        logging.info("Redirect notifications: from %s to %s", targets, new_targets)
        return new_targets

