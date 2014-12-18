#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''General math/aggregate functions
'''

from functools import partial
import functional
import math


def _percentile(N, percent, key=functional.id):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values

    >>> percentile([0,1], 0.5)
    0.5

    >>> percentile([0,1,2], 0.9)
    1.8

    >>> percentile([], 0.9) is None
    True
    """

    if not N:
        return None
    k = (len(N) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c - k)
    d1 = key(N[int(c)]) * (k - f)
    return d0 + d1


# median is 50th percentile.
_median = partial(_percentile, percent=0.5)


def median(results):
    return _median(sorted(results))


def percentile(results, percent):
    return _percentile(sorted(results), percent)


def apply_aggregate_function(results, func, key=functional.id, **args):
    '''
    >>> apply_aggregate_function([1,2,3], sum)
    6
    >>> apply_aggregate_function([{'a': 0}, {'a': 2}], _percentile, key=lambda x:x['a'], percent=0.9)
    1.8
    '''

    return func(map(key, results), **args)


def delta(results):
    '''
    >>> delta([])
    0

    >>> delta([0, 10])
    10

    >>> delta([10, 0])
    -10
    '''

    if not results:
        # no results => zero delta
        return 0
    return results[-1] - results[0]


def avg(results):
    '''
    >>> avg([]) is None
    True

    >>> avg([0, 1])
    0.5
    '''

    if not results:
        return None
    return sum(results) * 1.0 / len(results)


def first(results):
    '''
    >>> first([1, 2])
    1

    >>> first([]) is None
    True
    '''

    return (results[0] if results else None)


def _min(results):
    '''
    >>> _min([2, 1, 3, 2])
    1

    >>> _min([]) is None
    True
    '''

    return (min(results) if results else None)


def _max(results):
    '''
    >>> _max([2, 1, 3, 2])
    3

    >>> _max([]) is None
    True
    '''

    return (max(results) if results else None)


