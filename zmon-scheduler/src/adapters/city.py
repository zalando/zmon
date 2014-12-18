#!/usr/bin/env python
# -*- coding: utf-8 -*-

from entity import EntityAdapter

import logging
import json


class CityAdapter(EntityAdapter):

    def __init__(self, path):
        super(CityAdapter, self).__init__()

        self.logger = logging.getLogger('zmon-scheduler.city-adapter')
        self.path = path

    def _get_entities(self):
        with open(self.path) as f:
            cities = json.load(f)

        for city in cities:
            city['type'] = 'city'
            city['id'] = self.get_entity_id('{}-{}'.format(city['country'], city['city']))

        return cities


