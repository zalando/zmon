#!/usr/bin/env python
# -*- coding: utf-8 -*-

from adapters import CityAdapter
from cmdb.client import Host, Client
from deployctl.client import Instance, DeployCtl, Project
from mock import patch, Mock, PropertyMock

import json
import os
import requests
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


def mock_hosts(self, *args, **kwargs):
    with open(os.path.join(DIR, 'fixtures/hosts.json')) as f:
        hosts = json.load(f)
    return [Host(h) for h in hosts if all(h.get(k) == v for (k, v) in kwargs.iteritems())]


def mock_instances(self, *args, **kwargs):
    with open(os.path.join(DIR, 'fixtures', 'instances.json')) as f:
        instances = json.load(f)
    return [Instance(i) for i in instances]


def mock_projects(self, *args, **kwargs):
    with open(os.path.join(DIR, 'fixtures', 'projects.json')) as f:
        projects = json.load(f)
    return [Project(p) for p in projects]


class TestAdapters(unittest.TestCase):

    @patch.object(Client, 'get_hosts', mock_hosts)
    def test_host(self):
        excluded = ['id', 'type', 'role_name']
        required = [
            'host',
            'external_ip',
            'internal_ip',
            'physical_machine_model',
            'virt_type',
            'team',
            'data_center_code',
        ]
        hosts = HostAdapter('cmdb.url')
        hosts.load_thread.start()
        hosts.load_thread.join()

        self.assertTrue(len(hosts.entities) > 0, 'Should load host entities')

        properties = hosts.properties()

        for e in excluded:
            self.assertNotIn(e, properties, 'Should not contain {} key in host properties'.format(e))

        for s in required:
            self.assertIn(s, properties, '{} should be in properties'.format(s))
            self.assertIsInstance(properties[s], set, '{} property should be a set'.format(s))
            self.assertTrue(len(properties[s]) > 0, '{} proerty should have values'.format(s))
            self.assertTrue(all(p for p in properties[s]), '{} property should not have empty values'.format(s))

        self.assertIsInstance(properties['host_role_id'], list, 'Hosts roles should be a list')
        self.assertTrue(len(properties['host_role_id']) > 0, 'Hosts roles should be generated')
        self.assertTrue(all('label' in p and 'value' in p for p in properties['host_role_id']),
                        'Hosts roles should contain label and value')


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

    @patch.object(DeployCtl, 'get_projects', mock_projects)
    def test_project(self):
        excluded = ['id', 'type']
        required = [
            'name',
            'team',
            'project_type',
            'instance_type',
            'deployable',
        ]
        possible_deployable_values = frozenset(['true', 'false'])
        projects = ProjectAdapter('url', 'user', 'password', 'real_user')
        projects.load_thread.start()
        projects.load_thread.join()

        self.assertTrue(len(projects.entities) > 0, 'Should load projects')
        # PF-3548
        self.assertTrue(all(p['deployable'] in possible_deployable_values for p in projects.entities),
                        'Should convert depluable flag to lower case string')

        properties = projects.properties()

        for e in excluded:
            self.assertNotIn(e, properties, 'Should not contain {} key in projects'.format(e))

        for r in required:
            self.assertIn(r, properties, '{} should be in properties'.format(r))
            self.assertIsInstance(properties[r], set, '{} property should be a set'.format(r))
            self.assertTrue(len(properties[r]) > 0, '{} property should have values'.format(r))


if __name__ == '__main__':
    unittest.main()
