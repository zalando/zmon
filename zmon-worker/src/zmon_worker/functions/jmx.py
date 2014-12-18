#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zmon_worker.errors import JmxQueryError

import json
import requests


class JmxWrapper(object):

    def __init__(self, host, port, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._queries = []

    @staticmethod
    def _transform_results(data):
        '''Transform JSON returned from JMX Query to a reasonable dict

        >>> JmxWrapper._transform_results({'results':[{'beanName':'mybean','attributes':{'HeapMemoryUsage':1}}]})
        {'HeapMemoryUsage': 1}
        >>> JmxWrapper._transform_results({'results':[{'beanName':'a','attributes':{'x':1}}, {'beanName': 'b', 'attributes': {'y': 2}}]})
        {'a': {'x': 1}, 'b': {'y': 2}}
        >>> JmxWrapper._transform_results({'results':[{'beanName':'a','attributes':{'x':{'compositeType': {}, 'contents': {'y':7}}}}]})
        {'x': {'y': 7}}
        '''

        results = data['results']
        d = {}
        for result in results:
            attr = result['attributes']
            for key, val in attr.items():
                if isinstance(val, dict) and 'compositeType' in val and 'contents' in val:
                    # special unpacking of JMX CompositeType objects (e.g. "HeapMemoryUsage")
                    # we do not want all the CompositeType meta information => just return the actual values
                    attr[key] = val['contents']
            d[result['beanName']] = attr
        if len(d) == 1:
            # strip the top-level "bean name" keys
            return d.values()[0]
        else:
            return d

    def query(self, bean, *attributes):
        self._queries.append((bean, attributes))
        return self

    def _jmxquery_queries(self):
        for bean, attributes in self._queries:
            query = bean
            if attributes:
                query += '@' + ','.join(attributes)
            yield query

    def results(self):
        if not self._queries:
            raise ValueError('No query to execute')

        r = requests.get('http://localhost:8074', params={'host': self.host, 'port': self.port,
                         'query': self._jmxquery_queries()})
        output = r.text
        try:
            data = json.loads(output)
        except:
            raise JmxQueryError(output)
        return self._transform_results(data)


if __name__ == '__main__':
    # example call:
    # JAVA_HOME=/opt/jdk1.7.0_21/ python jmx.py restsn03 49600 jmxremote.password java.lang:type=Memory HeapMemoryUsage
    import sys
    jmx = JmxWrapper(*sys.argv[1:4])
    print jmx.query(*sys.argv[4:]).results()
