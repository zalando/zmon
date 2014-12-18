#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query Tomcat metrics via JMX
"""

from http import HttpWrapper
from jmx import JmxWrapper
from counter import CounterWrapper
from functools import partial
import json
import sys

MILLI = 10 ** -3
NANO = 10 ** -9

THREAD_POOL_PORT_PREFIXES = {'http': 3, 'ajp': 2}


def memory_usage_percentage(data):
    '''helper function to calculate percentage from "used" and "max"'''

    return round(100. * data['used'] / data['max'], 2)


class ZomcatWrapper(object):

    def __init__(self, host, instance, http, jmx, counter):
        '''expects ready to use "partials" for http, jmx and counter'''

        self.host = host
        self.instance = instance
        self._http = http
        self._jmx = jmx
        # initialize counter with Redis connection
        self._counter = counter('')

    @staticmethod
    def get_jmx_port(instance):
        return int('4' + instance)

    def gc(self):
        '''return garbage collector statistics: gc_percentage and gcs_per_sec'''

        gc_count = 0
        gc_time = 0
        for _type in 'ConcurrentMarkSweep', 'ParNew':
            try:
                row = self._jmx().query('java.lang:type=GarbageCollector,name={}'.format(_type), 'CollectionCount',
                                        'CollectionTime').results()
                gc_count += row['CollectionCount']
                gc_time += row['CollectionTime']
            except:
                pass

        gc_count = round(self._counter.key('gcCount').per_second(gc_count), 2)
        gc_time = self._counter.key('gcTime').per_second(gc_time * MILLI)
        return {'gc_percentage': round(gc_time * 100, 2), 'gcs_per_sec': gc_count}

    def requests(self):
        '''return Tomcat request statistics such as requests/s and errors/s'''

        request_count = 0
        request_time = 0
        http_errors = 0
        for _type, _port_prefix in THREAD_POOL_PORT_PREFIXES.items():
            try:
                row = self._jmx().query('Catalina:type=GlobalRequestProcessor,name="{}-apr-{}{}"'.format(_type,
                                        _port_prefix, self.instance), 'requestCount', 'processingTime', 'errorCount'
                                        ).results()
                request_count += row['requestCount']
                request_time += row['processingTime']
                http_errors += row['errorCount']
            except:
                pass
        requests = round(self._counter.key('requestCount').per_second(request_count), 2)
        http_errors = round(self._counter.key('errorCount').per_second(http_errors), 2)
        time_per_request = round(self._counter.key('requestTime').per_second(request_time) / max(requests, 1), 2)

        return {'http_errors_per_sec': http_errors, 'requests_per_sec': requests, 'time_per_request': time_per_request}

    def basic_stats(self):
        '''return basic statistics such as memory, CPU and thread usage'''

        jmx = self._jmx()
        # {"NonHeapMemoryUsage":{"max":184549376,"init":24313856,"used":54467720,"committed":85266432},
        # "HeapMemoryUsage":{"max":518979584,"init":134217728,"used":59485272,"committed":129761280}}
        jmx.query('java.lang:type=Memory', 'HeapMemoryUsage', 'NonHeapMemoryUsage')
        jmx.query('java.lang:type=Threading', 'ThreadCount')
        jmx.query('java.lang:type=OperatingSystem', 'ProcessCpuTime')
        data = jmx.results()
        memory = data['java.lang:type=Memory']
        threading = data['java.lang:type=Threading']
        os = data['java.lang:type=OperatingSystem']
        cpu = self._counter.key('cpuTime').per_second(os['ProcessCpuTime'] * NANO)
        threads = threading['ThreadCount']

        try:
            heartbeat = self._http('/heartbeat.jsp', timeout=3).text().strip() == 'OK: Zalando JVM is running'
        except:
            heartbeat = None
        try:
            jobs = self._http('/jobs.monitor?view=json', timeout=3).json()['operationMode'] == 'NORMAL'
        except:
            jobs = None

        return {
            'cpu_percentage': round(cpu * 100, 2),
            'heap_memory_percentage': memory_usage_percentage(memory['HeapMemoryUsage']),
            'heartbeat_enabled': heartbeat,
            'jobs_enabled': jobs,
            'nonheap_memory_percentage': memory_usage_percentage(memory['NonHeapMemoryUsage']),
            'threads': threads,
        }

    def health(self):
        '''return complete Zomcat health statistics including memory, threads, CPU, requests and GC'''

        data = {}
        data.update(self.basic_stats())
        data.update(self.gc())
        data.update(self.requests())
        return data


if __name__ == '__main__':
    host = sys.argv[1]
    instance = sys.argv[2]
    http = partial(HttpWrapper, base_url='http://{host}:3{instance}/'.format(host=host, instance=instance))
    jmx = partial(JmxWrapper, host=host, port=ZomcatWrapper.get_jmx_port(instance))
    counter = partial(CounterWrapper, redis_host='localhost')
    zomcat = ZomcatWrapper(host, instance, http=http, jmx=jmx, counter=counter)
    print json.dumps(zomcat.health(), indent=4, sort_keys=True)
