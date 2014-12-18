#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis

STATISTIC_GAUGE_KEYS = frozenset([
    'blocked_clients',
    'connected_clients',
    'connected_slaves',
    'instantaneous_ops_per_sec',
    'used_memory',
    'used_memory_rss',
])
STATISTIC_COUNTER_KEYS = frozenset([
    'evicted_keys',
    'expired_keys',
    'keyspace_hits',
    'keyspace_misses',
    'total_commands_processed',
    'total_connections_received',
])


class RedisWrapper(object):

    '''Class to allow only readonly access to underlying redis connection'''

    def __init__(self, counter, host, port=6379, db=0):
        self._counter = counter('')
        self.__con = redis.StrictRedis(host, port, db)

    def llen(self, key):
        return self.__con.llen(key)

    def lrange(self, key, start, stop):
        return self.__con.lrange(key, start, stop)

    def get(self, key):
        return self.__con.get(key)

    def hget(self, key, field):
        return self.__con.hget(key, field)

    def hgetall(self, key):
        return self.__con.hgetall(key)

    def statistics(self):
        '''
        Return general Redis statistics such as operations/s

        Example result::

            {
                "blocked_clients": 2,
                "commands_processed_per_sec": 15946.48,
                "connected_clients": 162,
                "connected_slaves": 0,
                "connections_received_per_sec": 0.5,
                "dbsize": 27351,
                "evicted_keys_per_sec": 0.0,
                "expired_keys_per_sec": 0.0,
                "instantaneous_ops_per_sec": 29626,
                "keyspace_hits_per_sec": 1195.43,
                "keyspace_misses_per_sec": 1237.99,
                "used_memory": 50781216,
                "used_memory_rss": 63475712
            }
        '''

        data = self.__con.info()
        stats = {}
        for key in STATISTIC_GAUGE_KEYS:
            stats[key] = data.get(key)
        for key in STATISTIC_COUNTER_KEYS:
            stats['{}_per_sec'.format(key).replace('total_', '')] = \
                round(self._counter.key(key).per_second(data.get(key, 0)), 2)
        stats['dbsize'] = self.__con.dbsize()
        return stats


if __name__ == '__main__':
    import sys
    import json
    from counter import CounterWrapper
    from functools import partial
    wrapper = RedisWrapper(partial(CounterWrapper, redis_host='localhost'), sys.argv[1])
    print json.dumps(wrapper.statistics(), indent=4, sort_keys=True)

