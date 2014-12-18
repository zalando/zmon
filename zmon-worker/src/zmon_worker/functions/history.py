#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wrapper for kairosdb to access history data about checks

import requests
from distance_to_history import DistanceWrapper

from settings import get_external_config


def get_request_json(check_id, entities, time_from, time_to, aggregator='avg', sampling_size_in_seconds=300):
    j = \
        """
{
  "metrics": [
    {
      "tags": {
        "entity": [
          %s
        ]
      },
      "name": "zmon.check.%s",
      "group_by": [
        {
          "name": "tag",
          "tags": [
            "key"
          ]
        }
      ],
      "aggregators": [
        {
          "name": "%s",
          "align_sampling": true,
          "sampling": {
            "value": "%s",
            "unit": "seconds"
          }
        }
      ]
    }
  ],
  "cache_time": 0,
  "start_relative": {
    "value": "%s",
    "unit": "seconds"
  },
  "end_relative": {
    "value": "%s",
    "unit": "seconds"
  }
}
"""

    r = j % (
        ','.join(map(lambda x: '"' + x + '"', entities)),
        check_id,
        aggregator,
        sampling_size_in_seconds,
        time_from,
        time_to,
    )
    return r


ONE_WEEK = 7 * 24 * 60 * 60
ONE_WEEK_AND_5MIN = ONE_WEEK + 5 * 60


class HistoryWrapper(object):

    def __init__(self, logger, check_id, entities):
        self.url = 'http://%s:%s/api/v1/datapoints/query' % (get_external_config().get('kairosdb.host', 'cassandra01'),
                get_external_config().get('kairosdb.port', '37629'))
        self.check_id = check_id
        self.logger = logger
        self.enabled = get_external_config().get('kairosdb.history_enabled', False)

        if type(entities) == list:
            self.entities = entities
        else:
            self.entities = [entities]

    def result(self, time_from=ONE_WEEK_AND_5MIN, time_to=ONE_WEEK):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        self.logger.info("history query %s %s %s", self.check_id, time_from, time_to)
        return requests.post(self.url, get_request_json(self.check_id, self.entities, int(time_from),
                             int(time_to))).json()

    def get_one(self, time_from=ONE_WEEK_AND_5MIN, time_to=ONE_WEEK):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        self.logger.info("history get one %s %s %s", self.check_id, time_from, time_to)
        return requests.post(self.url, get_request_json(self.check_id, self.entities, int(time_from),
                             int(time_to))).json()['queries'][0]['results'][0]['values']

    def get_aggregated(self, key, aggregator, time_from=ONE_WEEK_AND_5MIN, time_to=ONE_WEEK):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        # read the list of results
        query_result = requests.post(self.url, get_request_json(self.check_id, self.entities, int(time_from),
                                     int(time_to), aggregator, int(time_from - time_to))).json()['queries'][0]['results'
                ]

        # filter for the key we are interested in
        filtered_for_key = filter(lambda x: x['tags'].get('key', [''])[0] == key, query_result)

        if not filtered_for_key:
            return_value = []
        else:
            return_value = [filtered_for_key[0]['values'][0][1]]

        # since we have a sample size of 'all in the time range', return only the value, not the timestamp.
        return return_value

    def get_avg(self, key, time_from=ONE_WEEK_AND_5MIN, time_to=ONE_WEEK):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        self.logger.info("history get avg %s %s %s", self.check_id, time_from, time_to)
        return self.get_aggregated(key, 'avg', time_from, time_to)

    def get_std_dev(self, key, time_from=ONE_WEEK_AND_5MIN, time_to=ONE_WEEK):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        self.logger.info("history get std %s %s %s", self.check_id, time_from, time_to)
        return self.get_aggregated(key, 'dev', time_from, time_to)

    def distance(self, weeks=4, snap_to_bin=True, bin_size='1h', dict_extractor_path=''):
        if not self.enabled:
            raise Exception("History() function disabled for now")

        self.logger.info("history distance %s %s ", self.check_id, weeks, bin_size)
        return DistanceWrapper(history_wrapper=self, weeks=weeks, bin_size=bin_size, snap_to_bin=snap_to_bin,
                               dict_extractor_path=dict_extractor_path)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    zhistory = HistoryWrapper(17, ['GLOBAL'])
    r = zhistory.result()
    logging.info(r)
    r = zhistory.get_one()
    logging.info(r)
    r = zhistory.get_aggregated('', 'avg')
    logging.info(r)
