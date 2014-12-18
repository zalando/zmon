#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy
import datetime
from time_ import parse_timedelta


# from tasks.check import flatten

# originally, I wanted to load this function defintion from the tasks module, but I did not
# succeed in doing so. My python knowledge is limited, so maybe you can tell me how I can achieve this?

def flatten(structure, key='', path='', flattened=None):
    path = str(path)
    key = str(key)

    if flattened is None:
        flattened = {}
    if type(structure) not in (dict, list):
        flattened[((path + '.' if path else '')) + key] = structure
    elif isinstance(structure, list):
        pass
    else:
        #        for i, item in enumerate(structure):
        #            flatten(item, '%d' % i, '.'.join(filter(None, [path, key])), flattened)
        for new_key, value in structure.items():
            flatten(value, new_key, '.'.join(filter(None, [path, key])), flattened)
    return flattened


class DistanceWrapper(object):

    def __init__(self, history_wrapper, weeks=4, snap_to_bin=True, bin_size='1h', dict_extractor_path=''):

        self.history_wrapper = history_wrapper
        self.weeks = weeks
        self.snap_to_bin = snap_to_bin
        self.bin_size = parse_timedelta(bin_size)
        self.dict_extractor_path = dict_extractor_path

    def calculate_bin_time_range(self):
        '''
        Calculates the time ranges we need to look for using the settings configured for this class.
        Returns a list of dicts with the time ranges.
        '''

        now = datetime.datetime.now().replace(microsecond=0)
        if self.snap_to_bin:
            day_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # the number of bins (of size bin_size) that passed since the beginning of the day
            bins_this_day_until_now = int((now - day_begin).total_seconds() / self.bin_size.total_seconds())
            bin_begin = day_begin + bins_this_day_until_now * self.bin_size
            bin_end = day_begin + (bins_this_day_until_now + 1) * self.bin_size
        else:
            bin_begin = now - self.bin_size
            bin_end = now

        timestamps = []
        for week in range(1, self.weeks + 1):
            time_from = abs((bin_begin - week * datetime.timedelta(days=7) - now).total_seconds())
            time_to = abs((bin_end - week * datetime.timedelta(days=7) - now).total_seconds())
            timestamps.append({'time_from': time_from, 'time_to': time_to})
        return timestamps

    def extract_value(self, value):
        '''
        Extracts the value that will be used for comparisons. For dicts, we need an extractor. The extractor may not
        be empty if the value is a dict. The extractor is of the form 'a.b.c' for a dict with the structure
        {'a':{'b':{'c':5}}} to extract the value 5.
        '''

        if isinstance(value, dict):
            if self.dict_extractor_path == '':
                raise Exception('Extractor may not be empty for dicts as value. You need to tell which part of the dict I should use.'
                                )
            # throws when the key is unavailable; this is what we want
            value = flatten(value)[self.dict_extractor_path]
        return value

    def bin_mean(self):
        '''
        Calculates the mean of the history values. Applies the extractor and returns a scalar value.
        '''

        time_ranges = self.calculate_bin_time_range()
        averages = []
        for time_range in time_ranges:
            averages.extend(self.history_wrapper.get_avg(self.dict_extractor_path, time_range['time_from'],
                            time_range['time_to']))
        if not averages:
            raise Exception('No history data available in bin_mean call.')
        return numpy.average(averages)

    def bin_standard_deviation(self):
        '''
        Calculates the standard deviation of the history values. Applies the extractor and returns a scalar value.
        '''

        time_ranges = self.calculate_bin_time_range()
        deviations = []
        for time_range in time_ranges:
            deviations.extend(self.history_wrapper.get_std_dev(self.dict_extractor_path, time_range['time_from'],
                              time_range['time_to']))
        if not deviations:
            raise Exception('No history data available in bin_standard_deviation call.')

        # you can't simply average standard deviations.
        # see https://en.wikipedia.org/wiki/Variance#Basic_properties for details, keep in mind that
        # the different times are uncorrelated. We assume that the sample sizes for the different weeks
        # are equal (since we do not get exact sample sizes for a specific key from the kairosdb)
        return numpy.sqrt(numpy.sum(map(lambda x: x * x, deviations)))

    def absolute(self, value):
        '''
        Calculates the absolute distance of the actual value from the history value bins
        as selected through the constructor parameters weeks, bin_size and snap_to_bin.
        Applies the extractor and returns a scalar value.
        '''

        return self.extract_value(value) - self.bin_mean()

    def sigma(self, value):
        '''
        Calculates the relative distance of the actual value from the history value bins,
        normalized by the standard deviation. A sigma distance of 1.0 means that the actual value
        is as far away from the mean as the standard deviation is. The sigma distance can be negative, in this
        case you are below the mean with your value. If you need absolute values, you can use
        abs(sigma(value)). Applies the extractor and returns a scalar value.
        '''

        abs_value = self.absolute(value)
        std_dev = self.bin_standard_deviation()

        if std_dev == 0:
            return numpy.Infinity * numpy.sign(abs_value) if abs_value != 0 else numpy.float64(0)

        return abs_value / std_dev


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    logging.info('flattened dict: %s', flatten({'a': {'b': {'c': 5}}}))


    class HistoryWrapper(object):

        def __init__(self, check_id, entities=[]):
            self.check_id = check_id
            self.entities = entities

        @staticmethod
        def get_avg(key, time_from, time_to):
            return [7]

        @staticmethod
        def get_std_dev(key, time_from, time_to):
            return [2]


    now = datetime.datetime.now()
    before = now.replace(minute=0, second=0, microsecond=0)

    distance = DistanceWrapper(history_wrapper=HistoryWrapper(check_id=588), snap_to_bin=False, weeks=3, bin_size='5m')
    logging.info('Mean of history values: %f', distance.bin_mean())
    logging.info('Absolute distance: %f', distance.absolute(15))
    logging.info('Sigma distance: %f', distance.sigma(15))
