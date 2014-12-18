#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
ZMON 2.0 monitoring script.
This script checks if critical elements of ZMON's infrastructure are accessible.
Checked components:
- redis accessibility;
- kombu transport redis keys
- delay in publishing check results
Requirements:
- redis
'''

from argparse import ArgumentParser
from email.mime.text import MIMEText

import json
import redis
import smtplib
import time

CONFIG = {  # [seconds]
    'redis': {'host': 'localhost', 'port': 6379, 'db': 0},
    'required_keys': ['_kombu.binding.celeryev', '_kombu.binding.zmon', '_kombu.binding.celery.pidbox'],
    'required_result': 'zmon:checks:1:GLOBAL',
    'result_publish_delay': 30,
    'subject': 'ZMON 2 Critical Failure',
    'sender': 'zmon@example.com',
    'recipients': ['zmon-failure@example.com'],
}
EMAIL_BODY = u'''
ZMON 2 encountered a critical error. Please see below for details:
{}
'''


def get_redis_connection():
    r = redis.StrictRedis(**CONFIG['redis'])
    # Just creating an instance of StrictRedis doesn't actually do anything. We need to execute something to know if
    # the connection succeeded.
    r.info()
    return r


def redis_keys_exist(r, keys):
    p = r.pipeline()
    for key in keys:
        p.exists(key)
    return all(p.execute())


def results_published(r):
    last_results = r.lrange(CONFIG['required_result'], 0, 0)

    if not last_results:
        return False

    try:
        last_result = json.loads(last_results[0])
    except ValueError:
        return False

    return time.time() - last_result['ts'] < CONFIG['result_publish_delay']


def send_notification(host, port, messages):
    msg = MIMEText(EMAIL_BODY.format('\n'.join(messages)).encode('utf-8'), 'plain', 'utf-8')
    msg['Subject'] = CONFIG['subject']
    msg['From'] = 'ZMON 2 <{}>'.format(CONFIG['sender'])
    msg['To'] = ', '.join(CONFIG['recipients'])

    s = smtplib.SMTP(host, port)
    s.sendmail(CONFIG['sender'], CONFIG['recipients'], msg.as_string())
    s.quit()


def main(args):
    messages = []

    try:
        r = get_redis_connection()
    except Exception:
        messages.append('Cannot connect to redis on {host}:{port}/{db}'.format(**CONFIG['redis']))
    else:
        if not redis_keys_exist(r, CONFIG['required_keys']):
            messages.append('Cannot find required celery keys: {}'.format(','.join(CONFIG['required_keys'])))
        if not results_published(r):
            messages.append('Check results were not published in last {} s'.format(CONFIG['result_publish_delay']))

    if messages:
        send_notification(args.smtp_host, args.smtp_port, messages)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--smtp-host', help='SMTP host', default='localhost')
    parser.add_argument('--smtp-port', help='SMTP port', default=25, type=int)
    args = parser.parse_args()

    main(args)
