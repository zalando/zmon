#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from abc import ABCMeta, abstractmethod
from threading import Thread

import datetime

import re
import time
import kairosdb

class EntityAdapter(object):

    __metaclass__ = ABCMeta

    DEFAULT_UPDATE_INTERVAL = 253

    ENTITY_ID_RE = re.compile(r'[^a-zA-Z0-9\-_:@]')

    def __init__(self):
        self.entities = []
        self.excluded_properties = frozenset(['id', 'type'])
        self.load_thread = Thread(target=self.load)
        self.update_thread = Thread(target=self._update)
        self.update_thread.daemon = True
        self.update_interval = None

    @staticmethod
    def get_entity_id(entity_id):
        '''
        >>> EntityAdapter.get_entity_id('test entity id')
        'test_entity_id'

        >>> EntityAdapter.get_entity_id('validentity01')
        'validentity01'

        >>> EntityAdapter.get_entity_id('colons:are:ok dashes-too.no.dots')
        'colons:are:ok_dashes-too_no_dots'

        >>> EntityAdapter.get_entity_id('database@host')
        'database@host'
        '''

        return EntityAdapter.ENTITY_ID_RE.sub('_', entity_id)

    @staticmethod
    def get_normalized_environment(environment):
        '''
        >>> EntityAdapter.get_normalized_environment('perf-do')
        'performance-staging'

        >>> EntityAdapter.get_normalized_environment('integration')
        'integration'

        >>> EntityAdapter.get_normalized_environment('release')
        'release-staging'
        '''

        environment = EntityAdapter.ENVIRONMENT_WITHOUT_STRIPPABLE_AFFIXES_PATTERN.match(environment).group(1)
        environment = EntityAdapter.ENVIRONMENT_NORMALIZATIONS.get(environment, environment)
        return environment

    @staticmethod
    def get_normalized_team_name(team_name):
        '''
        >>> EntityAdapter.get_normalized_team_name('Zalando/Technology/Platform/Software')
        'Platform/Software'

        >>> EntityAdapter.get_normalized_team_name('Some/Other/Team')
        'Some/Other/Team'
        '''

        if team_name.startswith('Zalando/Technology/'):
            return team_name[19:]
        else:
            return team_name

    @abstractmethod
    def _get_entities(self):
        raise NotImplementedError

    def load(self):
        self.logger.info('Fetching entities ...')
        start = datetime.datetime.now()
        try:
            self.entities = self._get_entities()
        except Exception:
            self.logger.warn('Failed to load entities in %s', datetime.datetime.now() - start, exc_info=True)
        else:
            time_delta = datetime.datetime.now() - start
            self.logger.info('Got %s entities in %s', len(self.entities), time_delta)

            value = kairosdb.get_kairosdb_value("zmon.adapter.runtime",time.time(), time_delta.total_seconds(),{"adapter":self.__class__.__name__})            
            kairosdb.write_to_kairosdb([value])

    def _update(self):
        while True:
            time.sleep(self.update_interval or self.DEFAULT_UPDATE_INTERVAL)
            self.load()

    def properties(self):
        result = defaultdict(set)

        immutables = (
            int,
            long,
            float,
            bool,
            basestring,
            tuple,
        )

        for entity in self.entities:
            for k, v in entity.iteritems():
                if k not in self.excluded_properties:
                    if v is None or isinstance(v, immutables):
                        result[k].add(v)
                    elif isinstance(v, (list, set)):
                        result[k].add(tuple(v))
                    else:
                        self.logger.error('Error: entity adapter %s has non-hashable value in key %s, value %s',
                                          self.__class__.__name__, k, v)
                        return {}
        return result


