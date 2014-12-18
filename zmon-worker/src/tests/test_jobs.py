#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functions.http import HttpWrapper
from functions.jobs import JobsWrapper
from mock import patch

import unittest


def mock_json(self):
    return [
        {
            'duration': 0.011,
            'end': '2014-04-07 11:15:13',
            'end_seconds_ago': 33.8474,
            'instance': '9820',
            'limit': 1000,
            'name': 'importArticleFacetChangeFromZeosCatalogServiceJob',
            'processed': 0,
            'project': 'bm',
            'start': '2014-04-07 11:15:13',
            'start_seconds_ago': 33.8474,
        },
        {
            'duration': 0.002,
            'end': '2014-04-07 11:15:09',
            'end_seconds_ago': 37.8474,
            'instance': '9820',
            'limit': None,
            'name': 'translationEventConsumerJob',
            'processed': None,
            'project': 'bm',
            'start': '2014-04-07 11:15:09',
            'start_seconds_ago': 37.8474,
        },
        {
            'duration': 0.003,
            'end': '2014-04-07 11:15:09',
            'end_seconds_ago': 37.8475,
            'instance': '9820',
            'limit': 1000,
            'name': 'synchronizeChangesJob',
            'processed': 0,
            'project': 'bm',
            'start': '2014-04-07 11:15:09',
            'start_seconds_ago': 37.8475,
        },
        {
            'duration': 0.476,
            'end': '2014-04-07 11:15:09',
            'end_seconds_ago': 37.8475,
            'instance': '9820',
            'limit': None,
            'name': 'processIncomingDocdataFilesJob',
            'processed': None,
            'project': 'bm',
            'start': '2014-04-07 11:15:08',
            'start_seconds_ago': 38.8475,
        },
        {
            'duration': 0.312,
            'end': '2014-04-07 11:15:09',
            'end_seconds_ago': 37.8475,
            'instance': '9820',
            'limit': None,
            'name': 'processExportedZalosArticlesJob',
            'processed': None,
            'project': 'bm',
            'start': '2014-04-07 11:15:08',
            'start_seconds_ago': 38.8475,
        },
        {
            'duration': 0.009,
            'end': '2014-04-07 11:15:09',
            'end_seconds_ago': 37.8475,
            'instance': '9820',
            'limit': 1000,
            'name': 'importArticleFacetChangeFromZeosCatalogServiceJob',
            'processed': 0,
            'project': 'bm',
            'start': '2014-04-07 11:15:08',
            'start_seconds_ago': 38.8475,
        },
    ]


class JobsWrapperTest(unittest.TestCase):

    @patch.object(HttpWrapper, 'json', mock_json)
    def test_lastruns(self):
        j = JobsWrapper('live', 'bm')
        lastruns = j.lastruns()

        self.assertIsInstance(lastruns, dict)
        self.assertTrue(all(isinstance(v, dict) for (k, v) in lastruns.iteritems()))
        self.assertEqual(lastruns['importArticleFacetChangeFromZeosCatalogServiceJob']['start_seconds_ago'], 33.8474,
                         'Should contain the latest run')

    @patch.object(HttpWrapper, 'json', mock_json)
    def test_history(self):
        j = JobsWrapper('live', 'bm')
        history = j.history()

        self.assertIsInstance(history, dict)
        self.assertTrue(all(isinstance(v, list) for (k, v) in history.iteritems()))
        self.assertEquals(len(history['importArticleFacetChangeFromZeosCatalogServiceJob']), 2)


if __name__ == '__main__':
    unittest.main()
