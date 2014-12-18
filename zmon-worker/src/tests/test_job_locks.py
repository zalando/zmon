#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cmdb.client import Client, Host
from functions.joblocks import JoblocksWrapper
from mock import patch, Mock

import json
import time
import unittest


def mock_hosts(self, *args, **kwargs):
    return [Host(
        id=2864,
        aliases=None,
        assigned_memory=2097152,
        assigned_processor_cores=1,
        audit_status=u'OK',
        created=u'2014-03-25T11:08:27.507330',
        created_by=u'zcloud.py',
        description=u'Redis job locking node (PF-3108)',
        external_ip=u'10.64.32.156',
        host_role_id=118,
        hostname=u'lock01',
        lifecycle_status_id=6000,
        parent_host_id=1394,
        physical_machine_id=848,
        role={'description': 'Redis lock node for redis-based job locking (PF-3108)'},
    ), Host(
        id=2865,
        aliases=None,
        assigned_memory=2097152,
        assigned_processor_cores=1,
        audit_status=u'OK',
        created=u'2014-03-25T11:08:27.507330',
        created_by=u'zcloud.py',
        description=u'Redis job locking node (PF-3108)',
        external_ip=u'10.64.32.156',
        host_role_id=118,
        hostname=u'lock02',
        lifecycle_status_id=6000,
        parent_host_id=1394,
        physical_machine_id=848,
        role={'description': 'Redis lock node for redis-based job locking (PF-3108)'},
    )]


def mock_valid_locks():
    return ['''{
  "created": "2014-04-11T11:44:39",
  "host": "localhost",
  "instanceCode": "9305",
  "lockingComponent": "translationCacheStatsUpdateJob2",
  "resource": "TranslationCacheStatsUpdateJob2",
  "expectedMaximumDuration": 60000,
  "flowId": "flowId"
}''',
            '''{
  "created": "2014-04-11T11:45:39",
  "host": "localhost",
  "instanceCode": "9305",
  "lockingComponent": "translationCacheStatsUpdateJob",
  "resource": "TranslationCacheStatsUpdateJob",
  "expectedMaximumDuration": 60000
}''']


def mock_invalid_locks():
    return ['''{
  "created": "2014-04-11T11:44:39",
  "host": "localhost",
  "instanceCode": "9305",
  "lockingComponent": "translationCacheStatsUpdateJob2",
  "resource": "TranslationCacheStatsUpdateJob2",
  "expectedMaximumDuration": 60000
}''',
            '''{
  "created": "2014-0
  "host": "localhost",
  "instanceCode": "9305",
  "lockingComponent": "translationCacheStatsUpdateJob",
  "resource": "TranslationCacheStatsUpdateJob",
  "expectedMaximumDuration": 60000
}''']


class JoblocksWrapperTest(unittest.TestCase):

    @patch.object(Client, 'get_hosts', mock_hosts)
    @patch('redis.StrictRedis')
    def test_locks(self, redis_mock):
        j = JoblocksWrapper(cmdb_url='test', project='test')
        locks = [json.loads(lock) for lock in mock_valid_locks()]
        instance = redis_mock.return_value
        pipeline = Mock()
        pipeline.execute.return_value = mock_valid_locks()
        instance.pipeline.return_value = pipeline

        with patch.object(time, 'time') as mock_time:
            # Mock the current time, the first lock should be marked as expired, the second one shouldn't.
            mock_time.return_value = time.mktime(time.strptime(locks[1]['created'], '%Y-%m-%dT%H:%M:%S')) + 5
            results = j.results()

        self.assertIsInstance(results, dict)
        self.assertEquals(len(results), 2)
        self.assertTrue(results['translationCacheStatsUpdateJob2']['expired'])
        self.assertFalse(results['translationCacheStatsUpdateJob']['expired'])
        self.assertTrue(all('flow_id' in r for r in results.itervalues()))
        self.assertEquals('flowId', results['translationCacheStatsUpdateJob2']['flow_id'])
        self.assertEquals('', results['translationCacheStatsUpdateJob']['flow_id'])

    @patch.object(Client, 'get_hosts', mock_hosts)
    @patch('redis.StrictRedis')
    def test_invalid_json(self, redis_mock):
        j = JoblocksWrapper(cmdb_url='test', project='test')
        instance = redis_mock.return_value
        pipeline = Mock()
        pipeline.execute.return_value = mock_invalid_locks()
        instance.pipeline.return_value = pipeline

        results = j.results()

        self.assertEquals(len(results), 1)


if __name__ == '__main__':
    unittest.main()
