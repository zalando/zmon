#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import Mock
from scmimport import fileimport

import unittest


class TestImport(unittest.TestCase):

    def setUp(self):
        self.soap_client = Mock()

    def tearDown(self):
        self.soap_client.reset_mock()

    def test_import(self):
        fileimport.import_from_stream(self.soap_client, {
            'name': 'test name',
            'description': 'test description',
            'entities': [{'type': 'GLOBAL'}],
            'interval': 60,
            'command': 'test command',
            'status': 'ACTIVE',
        }, 'http://test.zalando.net', 'test team', 'test user')

        self.assertTrue(self.soap_client.service.createOrUpdateCheckDefinition.called)

    def test_exception_handling(self):
        with self.assertRaises(fileimport.MalformedCheckDefinitionError):
            fileimport.import_from_stream(self.soap_client, {
                'name': 'test name',
                'description': 'test description',
                'entities': [{'type': 'GLOBAL'}],
                'command': 'test command',
                'status': 'ACTIVE',
            }, 'http://test.zalando.net', 'test team', 'test user')

        with self.assertRaises(fileimport.MalformedCheckDefinitionError):
            fileimport.import_from_stream(self.soap_client, {
                'name': 'test name',
                'description': 'test description',
                'interval': 60,
                'entities': [{'host': 'myhost123'}],
                'command': 'test command',
                'status': 'ACTIVE',
            }, 'http://test.zalando.net', 'test team', 'test user')


if __name__ == '__main__':
    unittest.main()
