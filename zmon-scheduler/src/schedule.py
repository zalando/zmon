#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import random

import json
import os
import time
import hashlib


def get_sleep_interval(interval, check_id):
    m = hashlib.sha1()
    m.update(str(check_id) + ' ' + str(interval))

    sleep_duration = int(m.hexdigest()[:4], 16)
    sleep_duration = int(sleep_duration * (interval / 65535.))

    return sleep_duration


class Schedule(object):

    SCHEDULE_FILENAME = 'last_schedule'
    DEFAULT_CHECK_INTERVAL = 60

    def __init__(self, path=None):
        self.path = path or Schedule.SCHEDULE_FILENAME
        self.loaded = False
        self._schedule = {}

    def load(self, check_definitions):
        '''
        Loads previously saved schedule from JSON or creates a new one based on given check definitions and their
        intervals, if the file is not found. The schedule is a dict containing the timestamp of check's last execution
        and defined downtimes, if any.
        Parameters
        ----------
        check_definitions: dict
            A dict of currently active check definitions where check_id is the key and check definition is the value.
        '''

        now = time.time()
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                saved_state = json.load(f)

            for check_id in saved_state:
                # This is a legacy check for schedule's structure. The first structure was flat, storing only timestamps
                # of check's last execution. After we added downtimes information, the structure became nested. This
                # condition can be removed after completely switching to the new structure (after the first deployment).
                if not isinstance(saved_state[check_id], dict):
                    saved_state[check_id] = {'last_run': saved_state[check_id]}

            if 'shutdown' in saved_state:
                del saved_state['shutdown']

            self._schedule = saved_state
        else:
            # To avoid running all checks at the same time at startup, we create a fake entry in the schedule. The fake
            # entry = current time + check interval * eps, where eps is a small random number form interval [0, 1).
            self._schedule = dict(cleanup={'last_run': now}, **dict((_id, {'last_run': now + min(check.interval,
                                  Schedule.DEFAULT_CHECK_INTERVAL) * random()}) for (_id, check) in
                                  check_definitions.iteritems()))
        self.loaded = True

    def save(self):
        '''
        Saves current schedule to JSON.
        '''

        with open(self.path, 'w') as f:
            json.dump(self._schedule, f)

    def set_downtime(self, check_id, downtime_id, start, end):
        if check_id in self._schedule:
            if 'downtimes' in self._schedule[check_id]:
                self._schedule[check_id]['downtimes'][downtime_id] = {'start': start, 'end': end, 'active': False}
            else:
                self._schedule[check_id]['downtimes'] = {downtime_id: {'start': start, 'end': end, 'active': False}}

    def remove_downtime(self, check_id, downtime_id, interval):
        if check_id in self._schedule and 'downtimes' in self._schedule[check_id] and downtime_id \
            in self._schedule[check_id]['downtimes']:
            # If the downtime was active (and it might be a long one), we should force the check reevaluation. We do
            # that by changing the last run timestamp, so the scheduler will execute the check in next iteration.
            if self._schedule[check_id]['downtimes'][downtime_id]['active']:
                self._schedule[check_id]['last_run'] = time.time() - interval
            del self._schedule[check_id]['downtimes'][downtime_id]

    def _downtime_started(self, check_id, ts):
        if check_id in self._schedule and 'downtimes' in self._schedule[check_id]:
            for d_id, definition in self._schedule[check_id]['downtimes'].items():
                if not definition['active'] and definition['start'] < ts:
                    self._schedule[check_id]['downtimes'][d_id]['active'] = True
                    return True
        return False

    def _downtime_ended(self, check_id, ts):
        if check_id in self._schedule and 'downtimes' in self._schedule[check_id]:
            for d_id, definition in self._schedule[check_id]['downtimes'].items():
                if definition['active'] and definition['end'] < ts:
                    del self._schedule[check_id]['downtimes'][d_id]
                    return True
        return False

    def get_next_time(self, check_id, interval):
        return self._schedule[check_id]['last_run'] + interval if check_id in self._schedule else time.time() + get_sleep_interval(check_id, interval)

    def store_last_run(self, check_id, time):
        if check_id in self._schedule:
            self._schedule[check_id]['last_run'] = time
        else:
            self._schedule[check_id] = {'last_run': time}

    def is_scheduled(self, check_id, interval):
        '''
        Tests whether check with given id and interval is scheduled for execution. This can be triggered by three
        events:
        - the difference between last execution's timestamp and current time is equal to check's interval;
        - there's a downtime defined for given check and that downtime is about to start;
        - there's a downtime defined for given check and that downtime is about to end.
        Parameters
        ----------
        check_id: int
            Check's id.
        interval: int
            Check's interval.
        '''

        now = time.time()

        if self._downtime_started(check_id, now) or self._downtime_ended(check_id, now):
            return True

        if check_id not in self._schedule and interval > 29 and interval < 901:
            self._schedule[check_id] = {'last_run': now + get_sleep_interval(interval, check_id) - interval}

        if ((self._schedule[check_id]['last_run'] if check_id in self._schedule else 0)) < now - interval:
            if check_id in self._schedule:
                self._schedule[check_id]['last_run'] = now
            else:
                self._schedule[check_id] = {'last_run': now}
            return True

        return False

    def mark_for_run(self, check_id):
        if check_id in self._schedule:
            self._schedule[check_id]['last_run'] = 0
        else:
            self._schedule[check_id] = {'last_run': 0}
