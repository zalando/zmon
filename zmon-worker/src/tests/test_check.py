#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import patch, Mock, PropertyMock
from tasks import check
from decimal import Decimal


class TestTasks(unittest.TestCase):

    def __init__(self, method_name='runTest'):
        # Workaround for codevalidator.
        self.setUp = self.set_up
        super(TestTasks, self).__init__(method_name)

    def set_up(self):
        self.mock = Mock()
        self.mock.con = 'redis connection'
        self.mock.request.timelimit = 30, 10
        self.mock.logger.debug.return_value = True
        self.mock.logger.info.return_value = True
        self.mock.send_metrics.return_value = True
        self.req = {
            'command': 'test(me)',
            'entity': {'id': 'entity_id'},
            'check_id': 'check_id',
            'check_name': 'check_name',
            'interval': 5,
            'schedule_time': 7,
        }
        p = PropertyMock(return_value='test')
        type(self.mock)._kairosdb_env = p

    def test_check(self):

        # Test regular check execution
        with patch.object(check, '_get_check_result', return_value={'ts': 8, 'td': 4, 'value': 42.0}):
            with patch.object(check, '_store_check_result') as mock_store_check_result:
                with patch.object(check, '_store_check_result_to_kairosdb') as mock_store_in_kairos:
                    result = check.check(self.mock, self.req)

                    self.assertIn('ts', result)
                    self.assertIn('td', result)
                    self.assertIn('value', result)
                    self.assertEquals(result['value'], 42.0)
                    mock_store_check_result.assert_called_once_with(self.mock.con, self.req, result)
                    mock_store_in_kairos.assert_called_once_with(self.mock, self.req, result)

    def test__store_check_result(self):
        con = Mock()

        # Test _store_check_result()
        req = {'check_id': 1, 'entity': {'id': 'e1'}}
        result = {'ts': 8, 'td': 4, 'value': 42.0}
        serialized_result = '{"td": 4, "ts": 8, "value": 42.0}'

        check._store_check_result(con, req, result)
        con.sadd.assert_any_call('zmon:checks', 1)
        con.sadd.assert_any_call('zmon:checks:1', 'e1')
        con.lpush.assert_called_with('zmon:checks:1:e1', serialized_result)

        # Test _store_check_result() with Decimal serialization
        result = {'ts': 8, 'td': 4, 'value': Decimal('42.0')}

        check._store_check_result(con, req, result)
        con.sadd.assert_any_call('zmon:checks', 1)
        con.sadd.assert_any_call('zmon:checks:1', 'e1')
        con.lpush.assert_called_with('zmon:checks:1:e1', serialized_result)

    def test_storing_results_to_kairos(self):
        req = {'check_id': 1, 'entity': {'id': 'e1'}}

        with patch.object(check.requests, 'post') as mock_post:
            with patch.object(check.json, 'dumps') as mock_json:
                r = Mock()
                r.status_code = 200
                mock_post.return_value = r
                check._store_check_result_to_kairosdb(self.mock, req, {'value': '5', 'ts': 5, 'td': 1})

                self.assertTrue(mock_post.called)
                mock_json.assert_called_once_with([{'name': 'zmon.check.1', 'datapoints': [[5000, 5.0]],
                                                  'tags': {'env': 'test', 'entity': 'e1'}}])

        # PF-3381 Test storing database checks results.
        self.mock.reset_mock()
        with patch.object(check.requests, 'post') as mock_post:
            with patch.object(check.json, 'dumps') as mock_json:
                value = {'value': {'load.1': '0.01', 'log.free': '49352708096',
                         'log.location': '/data/zalando/logs/postgres/pgsql_ja'}, 'ts': 4, 'td': 2}
                r = Mock()
                r.status_code = 200
                mock_post.return_value = r
                check._store_check_result_to_kairosdb(self.mock, req, value)

                self.assertTrue(mock_post.called)
                self.assertEquals(len(mock_json.call_args_list), 1, 'Should be called only once')
                self.assertEquals(len(mock_json.call_args[0][0]), 2, 'Should be called with two datasets')

                call_args = mock_json.call_args[0][0]

                self.assertEquals(call_args[0]['name'], 'zmon.check.1')
                self.assertDictEqual(call_args[0]['tags'], {'env': 'test', 'entity': 'e1', 'key': 'load.1'})
                self.assertListEqual(call_args[0]['datapoints'], [[4000, 0.01]])
                self.assertEquals(call_args[1]['name'], 'zmon.check.1')
                self.assertDictEqual(call_args[1]['tags'], {'env': 'test', 'entity': 'e1', 'key': 'log.free'})
                self.assertListEqual(call_args[1]['datapoints'], [[4000, 49352708096.0]])

        # PF-3490
        self.mock.reset_mock()
        with patch.object(check.requests, 'post') as mock_post:
            with patch.object(check.json, 'dumps') as mock_json:
                value = {'value': {
                    'str_value': '123.4',
                    'float_value': 323.3,
                    'int_value': 42,
                    'dict_value': {'in_dict_str': '123'},
                    'list_value': [1, 2, 3, 4],
                }, 'ts': 3, 'td': 1}
                r = Mock()
                r.status_code = 200
                mock_post.return_value = r
                check._store_check_result_to_kairosdb(self.mock, req, value)

                self.assertTrue(mock_post.called)

                expected = [{'datapoints': [[3000, 123.0]], 'name': 'zmon.check.1', 'tags': {'entity': 'e1',
                            'env': 'test', 'key': 'dict_value.in_dict_str'}}, {'datapoints': [[3000, 323.3]],
                            'name': 'zmon.check.1', 'tags': {'entity': 'e1', 'env': 'test', 'key': 'float_value'}},
                            {'datapoints': [[3000, 42.0]], 'name': 'zmon.check.1', 'tags': {'entity': 'e1',
                            'env': 'test', 'key': 'int_value'}}, {'datapoints': [[3000, 123.4]], 'name': 'zmon.check.1'
                            , 'tags': {'entity': 'e1', 'env': 'test', 'key': 'str_value'}}]

                # check for lists not being serialized
                self.assertTrue(filter(lambda x: x['tags'] == {'entity': 'e1', 'env': 'test', 'key': 'list_value.0'},
                                mock_json.call_args[0][0]) == [])

                # To make sure that the call arguments are what we expect, we sort them by key.
                self.assertListEqual(expected, sorted(mock_json.call_args[0][0], cmp=lambda a, b: cmp(a['tags']['key'],
                                     b['tags']['key'])))

        # PF-3506
        self.mock.reset_mock()
        with patch.object(check.requests, 'post') as mock_post:
            with patch.object(check.json, 'dumps') as mock_json:
                req['entity']['id'] = 'valentine@database'

                r = Mock()
                r.status_code = 200
                mock_post.return_value = r

                check._store_check_result_to_kairosdb(self.mock, req, {'value': '5', 'ts': 5, 'td': 1})

                self.assertTrue(mock_post.called)
                mock_json.assert_called_once_with([{'name': 'zmon.check.1', 'datapoints': [[5000, 5.0]],
                                                  'tags': {'env': 'test', 'entity': 'valentine_database'}}])


if __name__ == '__main__':
    unittest.main()
