#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zalando-specific function to monitor job locking (Job Framework uses Redis to lock)
"""

try:
    from cmdb.client import Client as cmdb_client
except:
    cmdb_client = None
from dogpile.cache import make_region

import json
import redis
import time

HOSTS_CACHE_EXPIRATION_TIME = 600  # 10 minutes
memory_cache = make_region().configure('dogpile.cache.memory', expiration_time=HOSTS_CACHE_EXPIRATION_TIME)


class JoblocksWrapper(object):

    LOCKING_NODE_ROLE_ID = 118
    ALLOCATED_STATUS_ID = 6000
    DEFAULT_EXPECTED_DURATION = 60000  # [ms]

    def __init__(self, cmdb_url, project=None, environment='LIVE'):
        if cmdb_client:
            self._cmdb = cmdb_client(cmdb_url)
        self.pattern = 'job:lock:{}:{}:*'.format(project or '*', environment)

    @memory_cache.cache_on_arguments(namespace='zmon-worker')
    def _get_hosts(self, host_role_id, lifecycle_status_id):
        return self._cmdb.get_hosts(host_role_id=host_role_id, lifecycle_status_id=lifecycle_status_id)

    @staticmethod
    def _get_expected_duration(redis_value, check_param):
        '''
        >>> JoblocksWrapper._get_expected_duration({}, None)
        60000.0
        >>> JoblocksWrapper._get_expected_duration({}, 10000)
        10000.0
        >>> JoblocksWrapper._get_expected_duration({'expectedMaximumDuration': 120000}, None)
        120000.0
        >>> JoblocksWrapper._get_expected_duration({'expectedMaximumDuration': 60000}, 90000)
        90000.0
        '''

        return float((check_param if check_param else redis_value.get('expectedMaximumDuration',
                     JoblocksWrapper.DEFAULT_EXPECTED_DURATION)))

    def results(self, expected_duration=None):
        hosts = self._get_hosts(JoblocksWrapper.LOCKING_NODE_ROLE_ID, JoblocksWrapper.ALLOCATED_STATUS_ID)
        host_connections = dict((host.hostname, redis.StrictRedis(host)) for host in hosts)
        host_keys = dict((host, con.keys(self.pattern)) for (host, con) in host_connections.iteritems())
        str_results = []

        for host, keys in host_keys.iteritems():
            p = host_connections[host].pipeline()
            for key in keys:
                p.get(key)
            str_results.extend(p.execute())

        results = []
        for r in str_results:
            try:
                results.append(json.loads(r))
            except ValueError:
                pass

        # In case flowId is None, we want to return empty string instead.
        return dict((r['lockingComponent'], {
            'host': r['host'],
            'instance': r['instanceCode'],
            'created': r['created'],
            'expected_duration': JoblocksWrapper._get_expected_duration(r, expected_duration),
            'flow_id': r.get('flowId') or '',
            'expired': time.time() - time.mktime(time.strptime(r['created'], '%Y-%m-%dT%H:%M:%S'))
                > JoblocksWrapper._get_expected_duration(r, expected_duration) / 1000,
        }) for r in results)


