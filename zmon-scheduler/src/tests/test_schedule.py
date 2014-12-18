#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import patch
from schedule import Schedule

import os
import time
import unittest

DIR = os.path.dirname(os.path.abspath(__file__))


class CheckDefinition(object):

    def __init__(self, entities_map, check_id, interval=60, command='', name='test'):
        self.entities_map = entities_map
        self.id = check_id
        self.interval = interval
        self.command = command
        self.name = name

    def __getitem__(self, key):
        return getattr(self, key)


class TestSchedule(unittest.TestCase):

    def test_initial_load(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/no_schedule.json'))
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 5
            schedule.load({'1': CheckDefinition([{'type': 'GLOBAL'}], 1), '2': CheckDefinition([{'type': 'host'}], 2,
                          10), '3': CheckDefinition([{'type': 'database'}], 3, 88400)})

        self.assertEqual(len(schedule._schedule), 4)
        self.assertEqual(schedule._schedule['cleanup']['last_run'], 5)
        self.assertTrue(all(check_id in schedule._schedule for check_id in ['1', '2', '3']))

        # Test initial schedule times
        self.assertGreaterEqual(schedule._schedule['1']['last_run'], 5)  # 60s is the default interval
        self.assertLess(schedule._schedule['1']['last_run'], 65)
        self.assertGreaterEqual(schedule._schedule['2']['last_run'], 5)
        self.assertLess(schedule._schedule['2']['last_run'], 15)
        self.assertGreaterEqual(schedule._schedule['3']['last_run'], 5)
        self.assertLess(schedule._schedule['3']['last_run'], 65)

    def test_load_old_format(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/old_schedule.json'))
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 5
            schedule.load({1: CheckDefinition([{'type': 'GLOBAL'}], 1), 2: CheckDefinition([{'type': 'host'}], 2, 10),
                          3: CheckDefinition([{'type': 'database'}], 3, 88400)})

        self.assertEqual(len(schedule._schedule), 4)
        self.assertNotIn('shutdown', schedule._schedule)
        self.assertTrue(all(check_id in schedule._schedule for check_id in ['cleanup', '1', '2', '3']))

        # Test loaded schedule times, checks' last runs timestamps = 3, 4, 5, cleanup = 2
        self.assertEqual(schedule._schedule['cleanup']['last_run'], 2)
        self.assertEqual(schedule._schedule['1']['last_run'], 3)
        self.assertEqual(schedule._schedule['2']['last_run'], 4)
        self.assertEqual(schedule._schedule['3']['last_run'], 5)

    def test_load_new_format(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/new_schedule.json'))
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 5
            schedule.load({1: CheckDefinition([{'type': 'GLOBAL'}], 1), 2: CheckDefinition([{'type': 'host'}], 2, 10),
                          3: CheckDefinition([{'type': 'database'}], 3, 88400)})

        self.assertEqual(len(schedule._schedule), 6)
        self.assertNotIn('shutdown', schedule._schedule)
        self.assertTrue(all(check_id in schedule._schedule for check_id in ['cleanup', '1', '2', '3']))

        # Test loaded schedule times, checks' (see fictures/new_schedule.json)
        self.assertEqual(schedule._schedule['cleanup']['last_run'], 2)
        self.assertEqual(schedule._schedule['1']['last_run'], 3)
        self.assertEqual(schedule._schedule['2']['last_run'], 4)
        self.assertEqual(schedule._schedule['2']['downtimes']['1']['start'], 3)
        self.assertEqual(schedule._schedule['2']['downtimes']['1']['end'], 5)
        self.assertEqual(schedule._schedule['3']['last_run'], 5)
        self.assertEqual(schedule._schedule['3']['downtimes']['2']['start'], 6)
        self.assertEqual(schedule._schedule['3']['downtimes']['2']['end'], 7)
        self.assertEqual(schedule._schedule['4']['last_run'], 6)
        self.assertEqual(schedule._schedule['4']['downtimes']['3']['start'], 2)
        self.assertEqual(schedule._schedule['4']['downtimes']['3']['end'], 5)
        self.assertEqual(schedule._schedule['4']['downtimes']['4']['start'], 4)
        self.assertEqual(schedule._schedule['4']['downtimes']['4']['end'], 10)
        self.assertEqual(schedule._schedule['5']['last_run'], 7)
        self.assertEqual(schedule._schedule['5']['downtimes']['5']['start'], 3)
        self.assertEqual(schedule._schedule['5']['downtimes']['5']['end'], 5)
        self.assertEqual(schedule._schedule['5']['downtimes']['6']['start'], 6)
        self.assertEqual(schedule._schedule['5']['downtimes']['6']['end'], 9)

    def test_schedule(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/no_schedule.json'))
        schedule._schedule = {
            1: {'last_run': 1},
            2: {'last_run': 11},
            3: {'last_run': 8, 'downtimes': {1: {'start': 10, 'end': 100, 'active': False}}},
            4: {'last_run': 1, 'downtimes': {2: {'start': 0, 'end': 11, 'active': True},
                'future_downtime': {'start': 9000, 'end': 9666, 'active': False}}},
        }

        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 12
            # Simple case, without downtimes, should be scheduled for next run
            self.assertTrue(schedule.is_scheduled(1, 10))
            self.assertEqual(schedule._schedule[1]['last_run'], 12)
            # Simple case, without downtimes, evaluated too soon, shouldn't be scheduled
            self.assertFalse(schedule.is_scheduled(2, 10))
            self.assertEqual(schedule._schedule[2]['last_run'], 11)
            # Complex case, evaluated too soon, but the downtime start should trigger scheduling.
            self.assertTrue(schedule.is_scheduled(3, 60))
            self.assertTrue(schedule._schedule[3]['downtimes'][1]['active'])
            self.assertEqual(schedule._schedule[3]['last_run'], 8)
            # Complex case, evaluated too soon, but the downtime end should trigger scheduling as well as removing
            # downtime entry from schedule. Future downtime definition should not be changed or removed.
            self.assertTrue(schedule.is_scheduled(4, 120))
            self.assertNotIn(2, schedule._schedule[4]['downtimes'])
            self.assertIn('future_downtime', schedule._schedule[4]['downtimes'])
            self.assertFalse(schedule._schedule[4]['downtimes']['future_downtime']['active'])
            self.assertEqual(schedule._schedule[4]['last_run'], 1)

    def test_set_downtimes(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/new_schedule.json'))
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 5
            schedule.load({1: CheckDefinition([{'type': 'GLOBAL'}], 1), 2: CheckDefinition([{'type': 'host'}], 2, 10),
                          3: CheckDefinition([{'type': 'database'}], 3, 88400)})
        schedule.set_downtime('1', 'new_downtime', 2, 10)

        self.assertIn('downtimes', schedule._schedule['1'])
        self.assertIn('new_downtime', schedule._schedule['1']['downtimes'])
        self.assertEqual(2, schedule._schedule['1']['downtimes']['new_downtime']['start'])
        self.assertEqual(10, schedule._schedule['1']['downtimes']['new_downtime']['end'])

        schedule.set_downtime('2', 'second_downtime', 3, 11)

        self.assertIn('downtimes', schedule._schedule['2'])
        self.assertIn('1', schedule._schedule['2']['downtimes'])
        self.assertIn('second_downtime', schedule._schedule['2']['downtimes'])
        self.assertEqual(3, schedule._schedule['2']['downtimes']['second_downtime']['start'])
        self.assertEqual(11, schedule._schedule['2']['downtimes']['second_downtime']['end'])

    def test_remove_downtimes(self):
        schedule = Schedule(path=os.path.join(DIR, 'fixtures/new_schedule.json'))
        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 5
            schedule.load({1: CheckDefinition([{'type': 'GLOBAL'}], 1), 2: CheckDefinition([{'type': 'host'}], 2, 10),
                          3: CheckDefinition([{'type': 'database'}], 3, 88400)})
        schedule.remove_downtime('2', '1', 10)

        self.assertNotIn('1', schedule._schedule['2']['downtimes'])

        schedule.remove_downtime('3', '1', 10)

        self.assertIn('downtimes', schedule._schedule['3'])
        self.assertIn('2', schedule._schedule['3']['downtimes'])

        with patch.object(time, 'time') as mock_time:
            mock_time.return_value = 11
            schedule.remove_downtime('3', '2', 10)

        self.assertNotIn('2', schedule._schedule['3']['downtimes'])
        self.assertEqual(1, schedule._schedule['3']['last_run'])


if __name__ == '__main__':
    unittest.main()
