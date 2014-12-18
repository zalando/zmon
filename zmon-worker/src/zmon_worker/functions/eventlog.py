#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zalando-specific function to query EventLog
"""

from zmon_worker.errors import CheckError
from http import HttpWrapper


class EventLogWrapper(object):

    '''Convenience wrapper to access EventLog counts'''

    def __init__(self):
        self.url = 'https://eventlog.example.com/'

    def __request(self, path, params):
        return HttpWrapper(self.url + path, params=params).json()

    def count(self, event_type_ids, time_from, time_to=None, group_by=None, **kwargs):
        '''Return number of events for given type IDs in given time frame

        returns a single number (integer) if only one type ID is given
        returns a dict (typeId as hex=>count) if more than one type ID is given
        returns a dict (fieldValue => count) if one type ID is given and a field name with "group_by"

        >>> EventLogWrapper().count('a', time_from='-1h')
        Traceback (most recent call last):
            ...
        CheckError: EventLog type ID must be a integer

        >>> EventLogWrapper().count(123, time_from='-1h')
        Traceback (most recent call last):
            ...
        CheckError: EventLog type ID is out of range
        '''

        if isinstance(event_type_ids, (int, long)):
            event_type_ids = [event_type_ids]
        for type_id in event_type_ids:
            if not isinstance(type_id, (int, long)):
                raise CheckError('EventLog type ID must be a integer')
            if type_id < 0x1001 or type_id > 0xfffff:
                raise CheckError('EventLog type ID is out of range')
        params = kwargs
        params['event_type_ids'] = ','.join(['{:x}'.format(v) for v in event_type_ids])
        params['time_from'] = time_from
        params['time_to'] = time_to
        params['group_by'] = group_by
        result = self.__request('count', params)
        if len(event_type_ids) == 1 and not group_by:
            return result.get(params['event_type_ids'], 0)
        else:
            return result


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    eventlog = EventLogWrapper()
    print eventlog.count(0x96001, time_from='-1m')
    print eventlog.count([0x96001, 0x63005], time_from='-1m')
    print eventlog.count(0x96001, time_from='-1m', group_by='appDomainId')
