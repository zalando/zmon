#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from notification import BaseNotification
import eventlog
import logging

logger = logging.getLogger(__name__)


SMS_PROVIDER_URL = 'https://gateway.smstrade.de'
SMS_SENDER = 'zmon2'
SMS_API_KEY = ''
SMS_ROUTE = 'gold'
SMS_MAXLENGTH = 2048

#logger = get_task_logger('zmon-worker')


class SmsException(Exception):

    pass


class Sms(BaseNotification):

    @classmethod
    def send(cls, alert, *args, **kwargs):
        provider_url = cls._config.get('notifications.sms.provider_url', SMS_PROVIDER_URL)
        phone_numbers = BaseNotification.resolve_group(args, phone=True)
        repeat = kwargs.get('repeat', 0)

        maxlen = cls._config.get('notifications.sms.maxlength', SMS_MAXLENGTH)
        message = cls._get_subject(alert, custom_message=kwargs.get('message'))[:maxlen]

        request_params = {
            'to': '',
            'key': cls._config['notifications.sms.apikey'],
            'from': cls._config.get('notifications.sms.sender', SMS_SENDER),
            'route': cls._config.get('notifications.sms.route', SMS_ROUTE),
            'message': message,
            'cost': 1,
            'message_id': 1,
        }

        alert_id = alert.get('alert_def', {}).get('id', 0)
        entity = alert.get('entity', {}).get('id', 0)

        try:
            if cls._config.get('notifications.sms.on', True):
                for phone in phone_numbers:
                    request_params['to'] = phone
                    r = requests.get(provider_url, params=request_params, verify=False)
                    url_secured = r.url.replace(request_params['key'], '*' * len(request_params['key']))
                    logger.info('SMS sent: request to %s --> status: %s, response headers: %s, response body: %s',
                                url_secured, r.status_code, r.headers, r.text)
                    r.raise_for_status()
                    eventlog.log(cls._EVENTS['SMS_SENT'].id, alertId=alert_id, entity=entity, phoneNumber=phone,
                                 httpStatus=r.status_code)
        except Exception:
            logger.exception('Failed to send sms for alert %s with id %s to: %s', alert['name'], alert['id'],
                             list(phone_numbers))
        finally:
            return repeat


if __name__ == '__main__':

    Sms.update_config({
        'notifications.sms.on': True,
        'notifications.sms.apikey': '--secret--',
        'notifications.sms.sender': 'zmon2',
        'notifications.sms.route': 'gold',
    })

    test_recipients = ['1stlevel']

    fake_alert = {
        'is_alert': True,
        'alert_def': {'name': 'Test'},
        'entity': {'id': 'hostxy'},
        'captures': {},
    }

    Sms.send(fake_alert, *test_recipients, **{'message': 'My customized zmon2 alert message'})
    Sms.send(fake_alert, *test_recipients)
