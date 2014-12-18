#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is intended as a quick and dirty drop in replacement of celery module, covering only
the functionality we use in zmon-scheduler.
In essence we are trying to cover this use case:
        req = {
            'command': each.command,
            'entity': entity,
            'check_id': each.id,
            'check_name': each.name,
            'interval': interval,
            'schedule_time': time.time(),
        }
        options = {
            'soft_time_limit': min(interval, 60 * 7),
            'time_limit': min(interval, 60 * 7) + 30,
            'expires': expires,
            'queue': queue,
            'routing_key': routing_key,
        }
        task = self.app.signature('check_and_notify', args=(req, self._generate_alerts(entity, each.id)), options=options)
        task.apply_async(task_id='check-{}-{}-{:.2f}'.format(each.id, entity['id'], time.time()))

"""

import base64
import json
import re
import time
from datetime import datetime, timedelta
import redis
from collections import namedtuple
from redis_context_manager import RedisConnHandler
import logging

LOGGER_NAME = 'zmon-scheduler'
_logger = None


def get_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger(LOGGER_NAME or __name__)
    return _logger


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


class Atask(object):

    DEFAULT_EXPIRE_INTERVAL = 300
    DEFAULT_SOFT_TIME_LIMIT = 60
    DEFAULT_HARD_TIME_LIMIT = 90

    def __init__(self, celery_app=None):
        self.celery_app = celery_app
        self.taskname = None
        self.args = []
        self.kwargs = {}
        self.options = {}
        self.task_id = ''

    def define_call(self, taskname, args=None, kwargs=None, options=None):
        self.taskname = taskname
        self.args = (args if args else [])
        self.kwargs = (kwargs if kwargs else {})
        self.options = (options if options else {})
        self.task_id = ''

    def apply_async(self, task_id=''):
        self.task_id = task_id
        # send task to redis
        self.celery_app.send_async(self)

    def task_body(self, task_id=None):
        return {
            'utc': True,
            'args': self.args,
            'retries': 0,
            'expires': self.get_expire_time_string(),
            'task': self.taskname,
            'timelimit': self.get_time_limits(),
            'kwargs': self.kwargs,
            'id': (task_id if task_id else self.task_id),
        }

    def get_queue_and_routing_key(self):
        return self.options['queue'], self.options['routing_key']

    def get_time_limits(self):
        return [self.options.get('time_limit', self.DEFAULT_HARD_TIME_LIMIT), self.options.get('soft_time_limit',
                self.DEFAULT_SOFT_TIME_LIMIT)]

    def get_expire_time_string(self, utc=True):
        '''
        Returns a formatted date string, example: '2014-09-04T10:27:32.919152+00:00'
        :param utc: use universal time
        :return: formatted date str
        '''

        interval = self.options.get('expires', self.DEFAULT_EXPIRE_INTERVAL)
        cur_time = (datetime.utcnow() if utc else datetime.now())
        expire_time = cur_time + timedelta(seconds=interval)
        return expire_time.strftime('%Y-%m-%dT%H:%M:%S.%f') + '+00:00'


class Control(object):

    def __init__(self, celery_app=None):
        self.celery_app = celery_app

    def purge(self):
        self.celery_app.purge()


class Celery(object):

    conf = {}

    _time_drop_task = 300

    def __init__(self, exchange='zmon'):
        self.exchange = exchange
        self.control = Control(celery_app=self)

    def signature(self, taskname, args=None, kwargs=None, options=None):
        task = Atask(celery_app=self)
        task.define_call(taskname, args=args, kwargs=kwargs, options=options)
        return task

    def purge(self):
        # TODO: close redis connection explicitly
        return 0

    def send_async(self, task):
        '''
        Push a task in the queue, retrying in case of connection error
        :param task: Atask instance
        :return:
        '''

        queue, routing_key, message = self._serialize_for_wire(task)
        t_init = time.time()
        while True:
            try:
                with RedisConnHandler.get_instance() as ch:
                    r_conn = ch.get_healthy_conn()
                    r_conn.rpush(queue, message)
                break
            except redis.ConnectionError:
                if time.time() - t_init > self._time_drop_task:
                    get_logger().error('About to drop task: %s, too many redis.ConnectionError', task.task_id)
                    raise

    def _serialize_for_wire(self, task):

        queue, routing_key = task.get_queue_and_routing_key()
        msg_obj = {
            'body': base64.b64encode(json.dumps(task.task_body())),
            'headers': {},
            'content-type': 'application/json',
            'content-encoding': 'utf-8',
            'properties': {'body_encoding': 'base64', 'correlation_id': task.task_id, 'delivery_info': {'priority': 0,
                           'routing_key': routing_key, 'exchange': self.exchange}},
        }

        return queue, routing_key, json.dumps(msg_obj)
