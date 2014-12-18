#!/usr/bin/env python
# -*- coding: utf-8 -*-

from adapters import CityAdapter
from mock import Mock

import json
import os
import unittest

DIR = os.path.dirname(os.path.abspath(__file__))


def mock_get_request(url):
    mock = Mock()
    if url.endswith('clusters'):
        with open(os.path.join(DIR, 'fixtures/clusters.json')) as f:
            data = json.load(f)
    else:
        with open(os.path.join(DIR, 'fixtures/databases.json')) as f:
            data = json.load(f)
    mock.json.return_value = data
    return mock


class TestAdapters(unittest.TestCase):

    def test_city(self):
        excluded = ['id', 'type']
        required = ['city', 'country', 'latitude', 'longitude']
        cities = CityAdapter(os.path.join(DIR, 'fixtures/cities.json'))
        cities.load_thread.start()
        cities.load_thread.join()

        self.assertTrue(len(cities.entities) > 0, 'Should load cities')

        properties = cities.properties()

        for e in excluded:
            self.assertNotIn(e, properties, 'Should not contain {} key in cities'.format(e))

        for r in required:
            self.assertIn(r, properties, '{} should be in properties'.format(r))
            self.assertIsInstance(properties[r], set, '{} property should be a set'.format(r))
            self.assertTrue(len(properties[r]) > 0, '{} property should have values'.format(r))


if __name__ == '__main__':
    unittest.main()
