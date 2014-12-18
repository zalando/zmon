#!/usr/bin/env python
# -*- coding: utf-8 -*-

import eventlog
import json
import logging
import time
import unittest

from mock import Mock, patch
from zmon_worker.tasks import cleanup, notify, ZmonTask
from zmon_worker.tasks.zmontask import manifest


class ResponseError(Exception):

    pass


class Redis(object):

    def __init__(self):
        self._storage = {}

    def delete(self, *args):
        result = 0
        for a in args:
            if a in self._storage:
                result += 1
                del self._storage[a]
        return result

    def get(self, key):
        return self._storage.get(key)

    def set(self, key, value):
        self._storage[key] = value
        return True

    def hdel(self, key, *args):

        if not args:
            raise ResponseError('wrong number of arguments for \'hdel\' command')

        result = 0
        if key in self._storage:
            for a in args:
                if a in self._storage[key]:
                    result += 1
                    del self._storage[key][a]
        return result

    def hlen(self, key):
        return (len(self._storage[key]) if key in self._storage else 0)

    def hget(self, key, field):
        return (self._storage[key].get(field) if key in self._storage else None)

    def hset(self, key, field, value):
        if key in self._storage:
            result = (0 if field in self._storage and value != self._storage[field] else 1)
            self._storage[key][field] = value
        else:
            result = 1
            self._storage[key] = {field: value}
        return result

    def hkeys(self, key):
        return (self._storage[key].keys() if key in self._storage else [])

    def hgetall(self, key):
        return (dict(self._storage[key]) if key in self._storage else {})

    def scard(self, key):
        return (len(self._storage[key]) if key in self._storage else 0)

    def smembers(self, key):
        return set((self._storage.get(key) if key in self._storage else []))

    def sadd(self, key, *args):
        if key in self._storage:
            self._storage[key].update(args)
            return (1 if any(a in self._storage[key] for a in args) else 0)
        else:
            self._storage[key] = set(args)
            return 1

    def srem(self, key, *args):
        if key in self._storage:
            result = (1 if any(a in self._storage[key] for a in args) else 0)
            for a in args:
                self._storage[key].discard(a)
            return result
        else:
            return 0

    def sismember(self, key, member):
        return key in self._storage and member in self._storage[key]

    def llen(self, key):
        return (len(self._storage[key]) if key in self._storage else 0)

    def lrange(self, key, start, stop):
        return (list((self._storage[key] if start == stop + 1 else list(self._storage[start:stop + 1]))) if key
                in self._storage else [])

    def rpush(self, key, *args):
        if key in self._storage:
            self._storage[key].extend(args)
        else:
            self._storage[key] = list(args)

    def pipeline(self):
        self._pipeline = Mock()
        self._pipeline.execute = self.execute
        return self._pipeline

    def execute(self):
        result = [getattr(self, c[0])(*c[1]) for c in self._pipeline.mock_calls]
        self._pipeline.mock_calls = []
        return result


class TestTasks(unittest.TestCase):

    def setUp(self):
        if hasattr(manifest, 'instance'):
            self._original_instance = manifest.instance
        manifest.instance = 'local'
        logger = logging.getLogger('zmon.test_tasks')
        logger.setLevel(logging.CRITICAL)
        self._orig_con = cleanup.cleanup._con
        self.mock_task = ZmonTask()
        self.mock_task._logger = logger
        self.mock_task._con = Redis()
        cleanup.cleanup._con = self.mock_task.con

    def tearDown(self):
        if hasattr(self, '_original_instance'):
            manifest.instance = self._original_instance
        self.mock_task._con._storage.clear()
        cleanup.cleanup._con = self._orig_con

    def test_downtimes_evaluation(self):
        now = time.time()
        self.mock_task.con.sadd('zmon:downtimes', '1', '2', '3')
        self.mock_task.con.sadd('zmon:downtimes:1', 'http01', 'http02')
        self.mock_task.con.sadd('zmon:downtimes:2', 'monitor03')
        self.mock_task.con.sadd('zmon:downtimes:3', 'cfgsn01', 'cfgsn02')

        # Regular, single downtime definition.
        self.mock_task.con.hset('zmon:downtimes:1:http01', '1', json.dumps({
            'start_time': now - 60 * 60,
            'end_time': now + 60 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))
        # Two downtime definitions, the first shouldn't match, but the second should.
        self.mock_task.con.hset('zmon:downtimes:1:http02', '2', json.dumps({
            'start_time': now - 15 * 60,
            'end_time': now - 5 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))
        self.mock_task.con.hset('zmon:downtimes:1:http02', '3', json.dumps({
            'start_time': now - 2 * 60,
            'end_time': now + 2 * 60,
            'created_by': 'deployctl',
            'comment': 'deployment',
        }))
        # Single definition that shouldn't match.
        self.mock_task.con.hset('zmon:downtimes:2:monitor03', '4', json.dumps({
            'start_time': now - 4 * 60,
            'end_time': now - 2 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))
        # Two definitions for two different entities, one matches, one doesn't.
        self.mock_task.con.hset('zmon:downtimes:3:cfgsn01', '5', json.dumps({
            'start_time': now - 8 * 60,
            'end_time': now - 2 * 60,
            'created_by': 'test',
            'comment': 'test_comment_doesnt_match',
        }))
        self.mock_task.con.hset('zmon:downtimes:3:cfgsn02', '6', json.dumps({
            'start_time': now - 8 * 60,
            'end_time': now + 2 * 60,
            'created_by': 'test',
            'comment': 'test_comment_match',
        }))

        eventlog.log = Mock()

        self.assertFalse(notify._evaluate_downtimes(self.mock_task, '100', 'monitor02'),
                         'Should not have scheduled downtime for non-existent alert id')
        self.assertFalse(notify._evaluate_downtimes(self.mock_task, '1', 'http03'),
                         'Should not have scheduled downtime for non-existent entity id')
        self.assertEquals('1', notify._evaluate_downtimes(self.mock_task, '1', 'http01')[0]['id'],
                          'Should have scheduled downtime')
        self.assertIn('1:http01:1', self.mock_task.con.smembers('zmon:active_downtimes'),
                      'Should save the first active downtime id in redis')
        eventlog.log.assert_called_with(notify.EVENTS['DOWNTIME_STARTED'].id, **{
            'alertId': '1',
            'entity': 'http01',
            'startTime': now - 60 * 60,
            'endTime': now + 60 * 60,
            'userName': 'test',
            'comment': 'test_comment',
        })

        # Test handling two definition, one active, one not
        self.assertEquals('3', notify._evaluate_downtimes(self.mock_task, '1', 'http02')[0]['id'],
                          'Should have scheduled downtime for multiple definitions if only one is matching')
        self.assertIn('1:http02:3', self.mock_task.con.smembers('zmon:active_downtimes'),
                      'Should save the second active downtime id in redis')
        eventlog.log.assert_called_with(notify.EVENTS['DOWNTIME_STARTED'].id, **{
            'alertId': '1',
            'entity': 'http02',
            'startTime': now - 2 * 60,
            'endTime': now + 2 * 60,
            'userName': 'deployctl',
            'comment': 'deployment',
        })
        self.assertIsNone(self.mock_task.con.hget('zmon:downtimes:1:http02', '2'),
                          'Should remove the definition of expired downtime')
        self.assertEquals(1, self.mock_task.con.hlen('zmon:downtimes:1:http02'),
                          'Should have one downtime definition in the hash remaining')
        self.assertTrue(self.mock_task.con.sismember('zmon:downtimes:1', 'http02'),
                        'Should not remove entity id if there is still one active downtime definition')

        # Test removing downtime that wasn't active
        self.assertFalse(notify._evaluate_downtimes(self.mock_task, '2', 'monitor03'),
                         'Should not have scheduled downtime for non matching definition')
        self.assertNotIn('4', self.mock_task.con.hgetall('zmon:downtimes:2:monitor03'),
                         'Should remove expired downtime definition that was not active')
        self.assertIsNone(self.mock_task.con.get('zmon:downtimes:2:monitor03'),
                          'Should remove the whole hash for no downtime definitions (1)')
        self.assertIsNone(self.mock_task.con.get('zmon:downtimes:2'),
                          'Should remove the set with entity ids for no downtime definitions (1)')
        self.assertFalse(self.mock_task.con.sismember('zmon:downtimes', '2'),
                         'Should remove alert id from set for no downtime definitions (1)')

        # Test removing downtime that was active
        self.mock_task.con.sadd('zmon:downtimes', '2')
        self.mock_task.con.sadd('zmon:downtimes:2', 'monitor03')
        self.mock_task.con.hset('zmon:downtimes:2:monitor03', '4', json.dumps({
            'start_time': now - 4 * 60,
            'end_time': now - 2 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))
        self.mock_task.con.sadd('zmon:active_downtimes', '2:monitor03:4')
        self.assertFalse(notify._evaluate_downtimes(self.mock_task, '2', 'monitor03'),
                         'Should not have scheduled downtime for expired definition')
        self.assertNotIn('2:monitor03:4', self.mock_task.con.smembers('zmon:active_downtimes'),
                         'Should remove scheduled downtime from redis')
        eventlog.log.assert_called_with(notify.EVENTS['DOWNTIME_ENDED'].id, **{
            'alertId': '2',
            'entity': 'monitor03',
            'startTime': now - 4 * 60,
            'endTime': now - 2 * 60,
            'userName': 'test',
            'comment': 'test_comment',
        })
        self.assertNotIn('4', self.mock_task.con.hgetall('zmon:downtimes:2:monitor03'),
                         'Should remove expired downtime definition that was previously active')
        self.assertIsNone(self.mock_task.con.get('zmon:downtimes:2:monitor03'),
                          'Should remove the whole hash for no downtime definitions (2)')
        self.assertIsNone(self.mock_task.con.get('zmon:downtimes:2'),
                          'Should remove the set with entity ids for no downtime definitions (2)')
        self.assertFalse(self.mock_task.con.sismember('zmon:downtimes', '2'),
                         'Should remove alert id from set for no downtime definitions (2)')

        # Test handling different downtimes on different entities.
        self.assertFalse(notify._evaluate_downtimes(self.mock_task, '3', 'cfgsn01'),
                         'Should not schedule a downtime for first entity')
        self.assertEquals('6', notify._evaluate_downtimes(self.mock_task, '3', 'cfgsn02')[0]['id'],
                          'Should schedule a downtime for second entity')
        self.assertNotIn('5', self.mock_task.con.hgetall('zmon:downtimes:3:cfgsn01'),
                         'Should remove key for no downtimes for the first entity')
        self.assertNotIn('cfgsn01', self.mock_task.con.smembers('zmon:downtimes:3'),
                         'Should remove the first entity from the set for no downtimes')
        self.assertIn('6', self.mock_task.con.hgetall('zmon:downtimes:3:cfgsn02'),
                      'Should not remove key for downtime for the second entity')
        self.assertIn('cfgsn02', self.mock_task.con.smembers('zmon:downtimes:3'),
                      'Should not remove the second entity from the set')
        self.assertIn('3', self.mock_task.con.smembers('zmon:downtimes'),
                      'Should not remove alert id from the set if only one downtime expired')

    # PF-3604 If one downtimes has expired, but there are future downtimes for the same alert-entity pair, they should
    # not be removed from redis.
    @patch.object(eventlog, 'log', lambda *args, **kwargs: True)
    def test_downtimes_removal(self):
        now = time.time()
        self.mock_task.con.sadd('zmon:downtimes', '1')
        self.mock_task.con.sadd('zmon:downtimes:1', 'http01')
        self.mock_task.con.sadd('zmon:active_downtimes', '1:http01:1')

        # Expired, but active
        self.mock_task.con.hset('zmon:downtimes:1:http01', '1', json.dumps({
            'start_time': now - 15 * 60,
            'end_time': now - 5 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))
        # Future
        self.mock_task.con.hset('zmon:downtimes:1:http01', '2', json.dumps({
            'start_time': now + 2 * 60,
            'end_time': now + 4 * 60,
            'created_by': 'deployctl',
            'comment': 'deployment',
        }))
        # Future
        self.mock_task.con.hset('zmon:downtimes:1:http01', '3', json.dumps({
            'start_time': now + 4 * 60,
            'end_time': now + 6 * 60,
            'created_by': 'test',
            'comment': 'test_comment',
        }))

        notify._evaluate_downtimes(self.mock_task, '1', 'http01')
        self.assertNotIn('1', self.mock_task.con.hgetall('zmon:downtimes:1:http01'))
        self.assertIn('2', self.mock_task.con.hgetall('zmon:downtimes:1:http01'))
        self.assertIn('3', self.mock_task.con.hgetall('zmon:downtimes:1:http01'))
        self.assertIn('http01', self.mock_task.con.smembers('zmon:downtimes:1'))
        self.assertIn('1', self.mock_task.con.smembers('zmon:downtimes'))

    def test_cleanup_disabled_checks(self):
        self.mock_task.con.sadd('zmon:checks', 1)
        self.mock_task.con.sadd('zmon:checks', 2)
        self.mock_task.con.sadd('zmon:checks:1', 'http01')
        self.mock_task.con.sadd('zmon:checks:1', 'http02')
        self.mock_task.con.sadd('zmon:checks:2', 'monitor03')
        self.mock_task.con.rpush('zmon:checks:1:http01', 'result01')
        self.mock_task.con.rpush('zmon:checks:1:http02', 'result02')
        self.mock_task.con.rpush('zmon:checks:2:monitor03', 'result03')

        # This means that the check with id 1 was disabled in controller and check with id 2 is still being used by
        # scheduler. List following the active check is the list of currently checked entities. For details see
        # zmon-scheduler -> update cleanup args method.
        cleanup.cleanup(disabled_checks=[1], check_entities={2: ['monitor03']})

        self.assertFalse(self.mock_task.con.sismember('zmon:checks', 1),
                         'Should remove the check from set of active checks')
        self.assertTrue(self.mock_task.con.sismember('zmon:checks', 2), 'Should not remove active check')
        self.assertFalse(self.mock_task.con.smembers('zmon:checks:1'), 'Should remove all entities for disabled check')
        self.assertIn('monitor03', self.mock_task.con.smembers('zmon:checks:2'),
                      'Should not remove entities for active check')
        self.assertIsNone(self.mock_task.con.get('zmon:checks:1:http01'), 'Should remove results for disabled check (1)'
                          )
        self.assertIsNone(self.mock_task.con.get('zmon:checks:1:http02'), 'Should remove results for disabled check (2)'
                          )
        self.assertIsNotNone(self.mock_task.con.lrange('zmon:checks:2:monitor03', 0, -1),
                             'Should not remove results for active check')

    def test_cleanup_disabled_alerts(self):
        self.mock_task.con.sadd('zmon:alerts', 1)
        self.mock_task.con.sadd('zmon:alerts', 2)
        self.mock_task.con.sadd('zmon:alerts:1', 'http01')
        self.mock_task.con.sadd('zmon:alerts:1', 'http02')
        self.mock_task.con.sadd('zmon:alerts:2', 'monitor03')
        self.mock_task.con.set('zmon:alerts:1:http01', 'result01')
        self.mock_task.con.set('zmon:alerts:1:http02', 'result02')
        self.mock_task.con.set('zmon:alerts:2:monitor03', 'result03')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http01', '{}')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http02', '{}')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http03', '{}')
        self.mock_task.con.hset('zmon:alerts:2:entities', 'monitor03', '{}')
        self.mock_task.con.hset('zmon:notifications:1:http01', 'notifications_key', 'timestamp')

        # Alert with id 1 was disabled in controller and alert with id 2 is still active for one entity.
        cleanup.cleanup(disabled_alerts=[1], alert_entities={2: ['monitor03']})

        self.assertFalse(self.mock_task.con.sismember('zmon:alerts', 1),
                         'Should remove the alert from set of active alerts')
        self.assertTrue(self.mock_task.con.sismember('zmon:alerts', 2), 'Should not remove active alert')
        self.assertFalse(self.mock_task.con.smembers('zmon:alerts:1'), 'Should remove all entities for disabled alert')
        self.assertIn('monitor03', self.mock_task.con.smembers('zmon:alerts:2'),
                      'Should not remove entities for active alert')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:http01'), 'Should remove results for disabled alert (1)'
                          )
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:http02'), 'Should remove results for disabled alert (2)'
                          )
        self.assertIsNotNone(self.mock_task.con.get('zmon:alerts:2:monitor03'),
                             'Should not remove results for active alert')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:entities'),
                          'Should remove set of all matching entities for disabled alert')
        self.assertEqual(len(self.mock_task.con.hkeys('zmon:alerts:2:entities')), 1,
                         'Should not remove matching entities from active alert')

        # PF-3116 Repeating notifications should also be handled by cleanup task
        self.assertIsNone(self.mock_task.con.get('zmon:notifications:1:http01'),
                          'Should remove repeating notifications for disabled alert')

    def test_cleanup_modified_checks(self):
        self.mock_task.con.sadd('zmon:checks', 1)
        self.mock_task.con.sadd('zmon:checks', 2)
        self.mock_task.con.sadd('zmon:checks:1', 'http01')
        self.mock_task.con.sadd('zmon:checks:1', 'http02')
        self.mock_task.con.sadd('zmon:checks:2', 'monitor03')
        self.mock_task.con.rpush('zmon:checks:1:http01', 'result01')
        self.mock_task.con.rpush('zmon:checks:1:http02', 'result02')
        self.mock_task.con.rpush('zmon:checks:2:monitor03', 'result03')

        # Only one check with id 1 is active for only one entity - http02. All other checks and entities should be
        # removed from redis.
        cleanup.cleanup(check_entities={1: ['http02']})

        self.assertTrue(self.mock_task.con.sismember('zmon:checks', 1), 'Should not remove active check')
        self.assertFalse(self.mock_task.con.sismember('zmon:checks', 2), 'Should remove inactive check')
        self.assertFalse(self.mock_task.con.sismember('zmon:check:1', 'http01'), 'Should remove inactive entity')
        self.assertTrue(self.mock_task.con.sismember('zmon:checks:1', 'http02'), 'Should not remove active entity')
        self.assertIsNone(self.mock_task.con.get('zmon:checks:1:http01'), 'Should remove results for inactive entity')
        self.assertIsNotNone(self.mock_task.con.lrange('zmon:checks:1:http02', 0, -1),
                             'Should not remove results for active entity')
        self.assertIsNone(self.mock_task.con.get('zmon:checks:2'), 'Should remove entities set for inactive check')
        self.assertIsNone(self.mock_task.con.get('zmon:checks:2:monitor03'), 'Should remove results for inactive check')

        # Edge case: check with no entities. This should remove all entries and empty sets from redis.
        cleanup.cleanup(check_entities={1: []})
        self.assertFalse(self.mock_task.con.sismember('zmon:checks', 1), 'Should remove the check without entities')
        self.assertIsNone(self.mock_task.con.get('zmon:checks:1'), 'Should remove the set of entity ids for no entities'
                          )
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:http02'), 'Should remove check results for no entities')

    def test_cleanup_modified_alerts(self):
        self.mock_task.con.sadd('zmon:alerts', 1)
        self.mock_task.con.sadd('zmon:alerts', 2)
        self.mock_task.con.sadd('zmon:alerts:1', 'http01')
        self.mock_task.con.sadd('zmon:alerts:1', 'http02')
        self.mock_task.con.sadd('zmon:alerts:2', 'monitor03')
        self.mock_task.con.set('zmon:alerts:1:http01', 'result01')
        self.mock_task.con.set('zmon:alerts:1:http02', 'result02')
        self.mock_task.con.set('zmon:alerts:2:monitor03', 'result03')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http01', '{}')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http02', '{}')
        self.mock_task.con.hset('zmon:alerts:1:entities', 'http03', '{}')
        self.mock_task.con.hset('zmon:alerts:2:entities', 'monitor03', '{}')
        self.mock_task.con.hset('zmon:notifications:1:http01', 'notification_key', 'timestamp')
        self.mock_task.con.hset('zmon:notifications:1:http02', 'notification_key', 'timestamp')

        # Only one alert with id 1 is active for two entities and only one entity (http02) is in alert state.
        cleanup.cleanup(alert_entities={1: ['http02', 'http03']})

        self.assertTrue(self.mock_task.con.sismember('zmon:alerts', 1), 'Should not remove active alert')
        self.assertFalse(self.mock_task.con.sismember('zmon:alerts', 2), 'Should remove inactive alert')
        self.assertFalse(self.mock_task.con.sismember('zmon:alerts:1', 'http01'), 'Should remove inactive entity')
        self.assertTrue(self.mock_task.con.sismember('zmon:alerts:1', 'http02'), 'Should not remove active entity')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:http01'), 'Should remove results for inactive entity')
        self.assertIsNotNone(self.mock_task.con.get('zmon:alerts:1:http02'),
                             'Should not remove results for active entity')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:2'), 'Should remove entities set for inactive alert')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:2:monitor03'), 'Should remove results for inactive alert')
        self.assertEqual(len(self.mock_task.con.hkeys('zmon:alerts:1:entities')), 2,
                         'Should not remove active entities from all matching entities set')
        self.assertIn('http02', self.mock_task.con.hkeys('zmon:alerts:1:entities'),
                      'Matching entities set chould contain the active entity (1)')
        self.assertIn('http03', self.mock_task.con.hkeys('zmon:alerts:1:entities'),
                      'Matching entities set chould contain the active entity (2)')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:2:entities'),
                          'Should remove matching entities set for inactive alert')
        self.assertIsNotNone(self.mock_task.con.get('zmon:notifications:1:http02'),
                             'Should not remove notifications for existing entity')

        # PF-3116 Handle repeating notifications for removed entities.
        self.assertIsNone(self.mock_task.con.get('zmon:notifications:1:http01'),
                          'Should remove repeating notifications for removed entities')

        # Edge case: alert with no entities. This should remove all entries and empty sets from redis.
        cleanup.cleanup(alert_entities={1: []})
        self.assertFalse(self.mock_task.con.sismember('zmon:alerts', 1), 'Should remove the alert without entities')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1'), 'Should remove the set of entities in alert')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:http02'), 'Should remove results for the entity')
        self.assertIsNone(self.mock_task.con.get('zmon:alerts:1:entities'), 'Should remove the set of all entities')
        self.assertIsNone(self.mock_task.con.get('zmon:notifications:1:http02'),
                          'Should remove notifications for no entities')


if __name__ == '__main__':
    unittest.main()
