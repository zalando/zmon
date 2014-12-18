#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zalando-specific function to query DeployCtl job information
"""

from http import HttpWrapper
from itertools import groupby
from operator import itemgetter


class JobsWrapper(object):

    def __init__(self, environment, project, **kwargs):
        self.url = 'https://deployctl.example.com/jobs/history.json/{}/{}'.format(environment, project)
        self.http_wrapper_params = kwargs
        self.name = itemgetter('name')

    def __request(self):
        return HttpWrapper(self.url, **self.http_wrapper_params).json()

    def lastruns(self):
        start_time = itemgetter('start_seconds_ago')

        return dict((job, min(runs, key=start_time)) for (job, runs) in groupby(sorted(self.__request(),
                    key=self.name), key=self.name))

    def history(self):
        return dict((job, list(runs)) for (job, runs) in groupby(sorted(self.__request(), key=self.name),
                    key=self.name))


