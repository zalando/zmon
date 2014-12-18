#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
import re

TIME_UNITS = {
    's': 'seconds',
    'm': 'minutes',
    'h': 'hours',
    'd': 'days',
}

TIME_FORMATS = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']

TIMEZONE_OFFSET = re.compile(r'([+-])([0-9][0-9])(?::?([0-9][0-9]))?$')


def parse_timedelta(s):
    '''
    >>> parse_timedelta('bla')


    >>> parse_timedelta('1s').total_seconds()
    1.0

    >>> parse_timedelta('-2s').total_seconds()
    -2.0

    >>> parse_timedelta('2m').total_seconds()
    120.0

    >>> parse_timedelta('1h').total_seconds()
    3600.0
    '''

    if s.startswith('-'):
        s = s[1:]
        factor = -1
    else:
        factor = 1
    try:
        v = int(s[:-1])
        u = s[-1]
    except:
        return None

    arg = TIME_UNITS.get(u)
    if arg:
        return factor * timedelta(**{arg: v})
    return None


def parse_datetime(s):
    '''
    >>> parse_datetime('foobar')

    >>> parse_datetime('1983-10-12T23:30').isoformat(' ')
    '1983-10-12 23:30:00'

    >>> parse_datetime('1983-10-12 23:30:12').isoformat(' ')
    '1983-10-12 23:30:12'

    >>> parse_datetime('2014-05-05 17:40:44.100313').isoformat(' ')
    '2014-05-05 17:40:44.100313'

    >>> parse_datetime('2014-05-05 17:40:44.100313+01:00').isoformat(' ')
    '2014-05-05 16:40:44.100313'
    '''

    s = s.replace('T', ' ')

    # calculate timezone data from date string, we'll parse it ourselves ('%z' is not supported on all platforms for strptime)
    match = TIMEZONE_OFFSET.search(s)
    if match:
        signum = int(match.group(1) + '1')
        hours = signum * int(match.group(2))
        minutes = signum * int(match.group(3))
        timezone_timedelta = timedelta(hours=hours, minutes=minutes)
    else:
        timezone_timedelta = timedelta()

    # remove timezone data from input string, if any.
    s = TIMEZONE_OFFSET.sub('', s)
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(s, fmt) - timezone_timedelta
        except:
            pass
    return None


class TimeWrapper(object):

    def __init__(self, spec='now', utc=False):
        now = (datetime.utcnow() if utc else datetime.now())
        delta = parse_timedelta(spec)
        if delta:
            self.time = now + delta
        elif spec == 'now':
            self.time = now
        else:
            self.time = parse_datetime(spec)

    def __sub__(self, other):
        '''
        >>> TimeWrapper('2014-01-01 01:01:25') - TimeWrapper('2014-01-01 01:01:01')
        24.0
        '''

        return (self.time - other.time).total_seconds()

    def isoformat(self, sep=' '):
        return self.time.isoformat(sep)

    def format(self, fmt):
        '''
        >>> TimeWrapper('2014-01-01 01:01').format('%Y-%m-%d')
        '2014-01-01'

        >>> TimeWrapper('-1m').format('%Y-%m-%d')[:3]
        '201'
        '''

        return self.time.strftime(fmt)


