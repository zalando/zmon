#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is intended as a quick and dirty drop in replacement of kombu module, covering only
the functionality we use in zmon. In essence we are trying to cover these use cases:
    from kombu.connection import Connection
    try:
        c = Connection(config['backend'])
    except KeyError:
        raise Exception('"backend" property missing in config object')

    r_conn = redis.StrictRedis(host=c.hostname, port=c.port, db=c.virtual_host)
And:
    from kombu import Queue
    app.conf.update(CELERY_QUEUES=(Queue('zmon:queue:default',routing_key='default'),
                    Queue('zmon:queue:secure', routing_key='secure'), Queue('zmon:queue:snmp', routing_key='snmp')))
"""

import re
from collections import namedtuple


class Queue(object):

    '''
    Used to emulate kombu Queue
    '''

    def __init__(self, queue, routing_key=None):
        self.queue = queue
        self.routing_key = routing_key


def parse_redis_conn(conn_str):
    '''
    Emulates kombu.connection.Connection that we were using only to parse redis connection string
    :param conn_str: example 'redis://localhost:6379/0'
    :return: namedtuple(hostname, port, virtual_host)
    '''

    Connection = namedtuple('Connection', 'hostname port virtual_host')
    conn_regex = r'redis://([-.a-zA-Z0-9_]+):([0-9]+)/([0-9]+)'
    m = re.match(conn_regex, conn_str)
    if not m:
        raise Exception('unable to parse redis connection string: {}'.format(conn_str))
    return Connection(m.group(1), int(m.group(2)), m.group(3))


