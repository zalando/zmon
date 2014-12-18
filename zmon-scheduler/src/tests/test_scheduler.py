#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import patch, Mock
from web import cherrypy, ZmonScheduler

import json
import os
import re
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


def mock_check_definitions(self):
    pass


def mock_alert_definitions(self):
    pass


def mock_wsclient(self):
    pass


def make_mock_redis_hget(expected_key, data):

    def hget(key, field):
        return (data.get(field) if data and key == expected_key else None)

    return hget


class MockSignature(object):

    def __call__(self, name, args, options):
        self.name = name
        self.args = args
        self.options = options
        return self

    def apply_async(self, task_id):
        self.task_id = task_id
        return self


def get_trial_run_request():
    with open(os.path.join(DIR, 'fixtures/trial_run_request.json')) as f:
        return json.load(f)


class CheckDefinition(object):

    def __init__(self, entities_map, check_id, interval=60, command='', name='test', entities_exclude_map=None):
        self.entities_map = entities_map
        self.entities_exclude_map = (entities_exclude_map if entities_exclude_map else [])
        self.id = check_id
        self.interval = interval
        self.command = command
        self.name = name

    def __getitem__(self, key):
        return getattr(self, key)

    def __str__(self):
        return '_'.join([
            str(self.entities_map),
            str(self.id),
            str(self.interval),
            str(self.command),
            str(self.name),
        ])


class TestScheduler(unittest.TestCase):

    def setUp(self):
        cherrypy.config.update({
            'cmdb.url': 'http://localhost:35600',
            'zmon.url': 'http://localhost:33400/ws/zMonWebService?wsdl',
            'cfgs.url': 'http://localhost:33600/ws/appDomainWebService?wsdl',
            'backend': 'DUMMY',
        })

    @patch.object(ZmonScheduler, '_load_check_definitions', mock_check_definitions)
    @patch.object(ZmonScheduler, '_load_alert_definitions', mock_alert_definitions)
    @patch.object(requests, 'get', mock_get_request)
    def test_generate_requests(self):
        scheduler = ZmonScheduler(os.getpid(), Mock())
        scheduler.alert_definitions = {
            1: {'check_id': 1, 'entities_map': [], 'entities_exclude_map': []},
            2: {'check_id': 2, 'entities_map': [], 'entities_exclude_map': []},
            3: {'check_id': 3, 'entities_map': [], 'entities_exclude_map': []},
            4: {'check_id': 4, 'entities_map': [], 'entities_exclude_map': []},
            5: {'check_id': 5, 'entities_map': [], 'entities_exclude_map': []},
            6: {'check_id': 6, 'entities_map': [], 'entities_exclude_map': []},
            7: {'check_id': 7, 'entities_map': [], 'entities_exclude_map': []},
        }
        scheduler.check_alert_map = {
            1: set([1]),
            2: set([2]),
            3: set([3]),
            4: set([4]),
            5: set([5]),
            6: set([6]),
            7: set([7]),
            8: set([8]),
            9: set([9]),
            10: set([10]),
            11: set([11, 12]),
        }
        self.assertIsNotNone(scheduler)

        # Test happy path: generate entities
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'city'}], 1), True))
        self.assertTrue(len(entities) > 0)
        for entity in entities:
            self.assertEqual('city', entity['type'])

        # Test check definition containing wrong keys (not present in instance).
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'lang': 'ruby', 'environment': 'space'}],
                        4), False))
        self.assertEquals(len(entities), 0)

        # Test combination with alert definitions entities filter, check definition specifies all hosts and alert
        # definition narrows it down to two entities.
        scheduler.alert_definitions[7] = {'check_id': 7, 'entities_map': [{'host': 'http01'}, {'host': 'http02'}]}
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'host'}], 7), False))
        self.assertEqual(len(entities), 2, 'Should generate entities based on check and alert filter')

        # Test another combination, this time alert entities should have no common subset with check entities, which
        # should result in empty result.
        scheduler.alert_definitions[8] = {'check_id': 8, 'entities_map': [{'type': 'zompy'}]}
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zomcat'}], 8), False))
        self.assertEqual(len(entities), 0, 'Should not have generated any entities')

        # Test redifining entities filter from check definition in alert definition, in this case, the entities
        # shouldn't be added twice.
        scheduler.alert_definitions[9] = {'check_id': 9, 'entities_map': [{'type': 'host', 'host': 'http01'}]}
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'host', 'host': 'http01'}], 9),
                        False))
        self.assertEqual(len(entities), 1, 'Should generate only one entity for the same filters')

        # Test mutually exclusive definitions, wider entity filter on alert definition should not add more entities
        # if the filter on check definition is narrower.
        scheduler.alert_definitions[10] = {'check_id': 10, 'entities_map': [{'type': 'zompy'}]}
        before_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zompy'}], 10), False)))
        scheduler.alert_definitions[10]['entities_map'] = [{'type': 'zompy'}, {'type': 'zomcat'}]
        after_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zompy'}], 10), False)))
        self.assertEqual(before_count, after_count,
                         'Should generate the same number of entities if alert filter is a superset of check filter')

        # Test multiple alert definitions, they shouldn't narrow down the overall number of generated entities. The
        # first check definition should generate check requests for type zomcat, environment live or type zomcat,
        # project shop without any alert definitions. The second one should generate check requests for type zomcat,
        # which then gets narrowed down to environment live and project shop by filter in alert definitions.
        scheduler.alert_definitions[11] = {'check_id': 11, 'entities_map': [{'project': 'shop'}]}
        scheduler.alert_definitions[12] = {'check_id': 11, 'entities_map': [{'environment': 'live'}]}
        single_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zomcat',
                           'environment': 'live'}, {'type': 'zomcat', 'project': 'shop'}], 1), False)))
        multiple_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zomcat'}], 11), False)))
        self.assertEqual(single_count, multiple_count,
                         'Should generate the same number of entities for multiple alert definitions')

        # Another test for multiple definitions: first we create a check definition with one alert definition, but no
        # entities filter, next we add another alert definition with entities filter. The second alert definition
        # should not affect the number of entities generated for this check.
        scheduler.alert_definitions[13] = {'check_id': 12, 'entities_map': []}
        scheduler.check_alert_map[12] = set([13])
        before_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zompy'}], 12), False)))
        scheduler.alert_definitions[14] = {'check_id': 12, 'entities_map': [{'environment': 'integration'}]}
        scheduler.check_alert_map[12] = set([13, 14])
        after_count = len(list(scheduler._generate_check_entities(CheckDefinition([{'type': 'zompy'}], 12), False)))
        self.assertEqual(before_count, after_count,
                         'Adding more specific alert definition should not reduce the number of generated entities')

        # Test new entity type - city
        scheduler.alert_definitions[15] = {'check_id': 13, 'entities_map': []}
        scheduler.check_alert_map[13] = set([15])
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'city'}], 13), False))
        self.assertEqual(20, len(entities), 'Should return all entities for type city')
        self.assertFalse(any(' ' in e['id'] for e in entities), 'Entities ids should not contain white spaces')

        # PF-3370 Test true/false values in entity filters
        scheduler.alert_definitions[16] = {'check_id': 14, 'entities_map': []}
        scheduler.check_alert_map[14] = set([16])
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'database_cluster_instance',
                        'pci': 'true'}], 14), False))
        self.assertTrue(len(entities) > 0, 'Should generate db cluster entities with pci environment')
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'database_cluster_instance',
                        'pci': 'false'}], 14), False))
        self.assertTrue(len(entities) > 0, 'Should generate db cluster entities without pci environment')
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'database_cluster_instance',
                        'port': '5432'}], 14), False))
        self.assertTrue(len(entities) > 0, 'Should generate db cluster entities with specified port')

    @patch.object(ZmonScheduler, '_load_check_definitions', mock_check_definitions)
    @patch.object(ZmonScheduler, '_load_alert_definitions', mock_alert_definitions)
    @patch.object(requests, 'get', mock_get_request)
    def test_generate_alerts(self):
        scheduler = ZmonScheduler(os.getpid(), Mock())
        entity = {
            'type': 'zomcat',
            'host': 'test',
            'id': 'test',
            'project': 'shop',
            'environment': 'integration',
        }
        # 1. type is zomcat or zompy => true
        # 2. environment is release-staging => false
        # 3. everything matches, except environment => false
        # 4. everything matches => true
        # 5. both match, but shouldn't be added twice => true
        scheduler.alert_definitions = {
            1: {'id': 1, 'entities_map': [{'type': 'zomcat'}, {'type': 'zompy'}], 'entities_exclude_map': []},
            2: {'id': 2, 'entities_map': [{'environment': 'release-staging'}], 'entities_exclude_map': []},
            3: {'id': 3, 'entities_map': [{'type': 'zomcat', 'project': 'shop', 'environment': 'live'}],
                'entities_exclude_map': []},
            4: {'id': 4, 'entities_map': [{'project': 'shop', 'environment': 'integration'}],
                'entities_exclude_map': []},
            5: {'id': 5, 'entities_map': [{'project': 'shop'}, {'host': 'test'}], 'entities_exclude_map': []},
        }
        # Mock check-alert map: one check definition with id 1 has five alert definitions.
        scheduler.check_alert_map = {1: set([
            1,
            2,
            3,
            4,
            5,
        ])}
        # Ids of matching alert definitions.
        ids = frozenset([1, 4, 5])

        result = scheduler._generate_alerts(entity, 1)

        self.assertEquals(len(result), 3, 'Three alert definitions should match given entity')
        self.assertTrue(all(r['id'] in ids for r in result), 'Should contain matching definitions')

        # Test if numbers are handled correctly
        scheduler.alert_definitions = {1: {'id': 1, 'entities_map': [{'host_role_id': '33'}], 'check_id': 1}}
        scheduler.check_alert_map = {1: set([1])}
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'city'}], 1), False))
        # It looks like doing the opposite, but we store entities for which we're able to generate an alert. This way
        # we can check later if the entities match the filter.
        matching = [e for e in entities if scheduler._generate_alerts(e, 1)]

        self.assertTrue(len(matching) > 0, 'Should generate entities matching the alert filter')

        # Test empty alert entities
        scheduler.alert_definitions = {1: {'id': 1, 'entities_map': [], 'check_id': 1}}
        scheduler.check_alert_map = {1: set([1])}
        check_alert = [scheduler._generate_alerts(e, 1) for e in entities]
        self.assertTrue(len(check_alert) > 0)
        self.assertEquals(len(entities), len(check_alert),
                          'Should generate as many alerts as check entities for empty alert entities')

        # Test matching teams in alert definitions, check definition should generate check entities for two teams
        # and alert definition should narrow it down to one.
        scheduler.check_alert_map = {2: [2]}
        scheduler.alert_definitions = {2: {'id': 2, 'check_id': 2, 'entities_map': [{'team': 'Platform/Software'}]}}
        entities = list(scheduler._generate_check_entities(CheckDefinition([{'type': 'host', 'team': 'Shop'},
                        {'type': 'host', 'team': 'Platform/Software'}], 2), False))
        matching = [e for e in entities if scheduler._generate_alerts(e, 2)]

        self.assertTrue(len(entities) > 0, 'Should generate entities for two teams')
        self.assertTrue(len(matching) > 0, 'Should generate entitites matching alert filter with one team')
        self.assertTrue(all('Platform/Software' in m['teams'] for m in matching), 'All entities should match one team')

    @patch.object(ZmonScheduler, '_load_check_definitions', mock_check_definitions)
    @patch.object(ZmonScheduler, '_load_alert_definitions', mock_alert_definitions)
    @patch.object(requests, 'get', mock_get_request)
    def test_cleanup(self):
        scheduler = ZmonScheduler(os.getpid(), Mock())
        scheduler.check_definitions = {1: CheckDefinition([{'type': 'city', 'city': 'Berlin'}], 1)}
        scheduler.alert_definitions = {1: {'id': 23, 'check_id': 1, 'entities_map': []}}

        scheduler.check_alert_map = {1: set([1])}

        # Sanity check
        self.assertIsNotNone(scheduler)

        # Test generating cleanup args for one host entity, the logic is the same for instances.
        scheduler._run_cleanup()
        self.assertIn(1, scheduler.cleanup['check_entities'], 'Cleanup args should contain active check definition id')
        self.assertIn('de-berlin', scheduler.cleanup['check_entities'][1],
                      'Cleanup args should contain entity id for given check definition id')

        # Simulate removing entity (e.g. decommissioning a host).
        for i in range(len(scheduler.hosts.entities)):
            if scheduler.hosts.entities[i]['host'] == 'http01':
                del scheduler.hosts.entities[i]
                break

        # Check whether cleanup args reflect changes after removing an entity.
        scheduler._run_cleanup()
        self.assertIn(1, scheduler.cleanup['check_entities'],
                      'Cleanup args should still contain active check definition id')
        self.assertNotIn('http01', scheduler.cleanup['check_entities'],
                         'Cleanup args should no longer contain removed entity id')

        # Test if modifying entities filter changes the cleanup args. Changes in entities filter should be directly
        # reflected in cleanup args, meaning that the entities that are no longer checked should not be in the args.
        scheduler.check_definitions[2] = CheckDefinition([{'type': 'zomcat'}], 2)
        scheduler.alert_definitions[2] = {'id': 42, 'check_id': 2, 'entities_map': []}
        scheduler.check_alert_map = {2: set([2])}

        # Test modifying entities filter on check definition. After narrowing down the entities filter, we should also
        # get less cleanup args for check_entities and alert_entities.
        scheduler._run_cleanup()
        before_checks_count = len(scheduler.cleanup['check_entities'][2])
        before_alerts_count = len(scheduler.cleanup['alert_entities'][2])
        scheduler.check_definitions[2] = CheckDefinition([{'type': 'zomcat', 'project': 'shop'}], 2)
        scheduler._run_cleanup()
        after_checks_count = len(scheduler.cleanup['check_entities'][2])
        after_alerts_count = len(scheduler.cleanup['alert_entities'][2])
        self.assertTrue(after_checks_count < before_checks_count,
                        'Cleanup args should contain less entities after changing check definition')
        self.assertTrue(after_alerts_count < before_alerts_count,
                        'Cleanup args for alerts should also change after changing check definition')

        # Test modifying entities filter on alert definition. After this modification, we should get less cleanup args
        # for alert_entities and check_entities.
        before_alerts = scheduler.cleanup['alert_entities'][2]
        scheduler.alert_definitions[2] = {'id': 5, 'check_id': 2, 'entities_map': [{'environment': 'live'}]}
        scheduler._run_cleanup()
        after_alerts = scheduler.cleanup['alert_entities'][2]
        self.assertTrue(after_alerts != before_alerts,
                        'Cleanup args for alerts should change after changing alert definition')

        # Test modifying filter on one of many alert definitions. After this modification, we should get less cleanup
        # args for modified alert_entities, but NOT for check_entities.
        scheduler.check_definitions[3] = CheckDefinition([{'type': 'zomcat'}], 3)
        scheduler.alert_definitions[3] = {'id': 300, 'check_id': 3, 'entities_map': []}
        scheduler.alert_definitions[4] = {'id': 400, 'check_id': 3, 'entities_map': []}
        scheduler.check_alert_map = {3: set([3, 4])}
        scheduler._run_cleanup()
        before_checks_count = len(scheduler.cleanup['check_entities'][3])
        before_alerts_count_first = len(scheduler.cleanup['alert_entities'][3])
        before_alerts_count_second = len(scheduler.cleanup['alert_entities'][4])
        scheduler.alert_definitions[4] = {'id': 1000, 'check_id': 3, 'entities_map': [{'project': 'shop'}]}
        scheduler._run_cleanup()
        after_checks_count = len(scheduler.cleanup['check_entities'][3])
        after_alerts_count_first = len(scheduler.cleanup['alert_entities'][3])
        after_alerts_count_second = len(scheduler.cleanup['alert_entities'][4])
        self.assertEqual(before_checks_count, after_checks_count,
                         'Cleanup args for checks should not change after changing one alert definition')
        self.assertEqual(before_alerts_count_first, after_alerts_count_first,
                         'Cleanup args for the first alert definition should not change after changing second alert')
        self.assertTrue(after_alerts_count_second < before_alerts_count_second,
                        'Cleanup args should be modified for the second alert definition after changing it')

        # Test exception handling for active alerts with inactive checks (PF-3184). We mock the inactive check by not
        # putting it in the dict. We don't store inactive checks in the scheduler (there's one alert with id 1 which
        # is assigned to check with id 1, but the check is not there).
        scheduler.check_definitions = {2: CheckDefinition([{'type': 'zomcat'}], 2)}
        scheduler.alert_definitions = {1: {'id': 123, 'check_id': 1, 'entities_map': []}}
        scheduler.check_alert_map = {1: set([1])}
        scheduler._run_cleanup()
        self.assertEqual(1, len(scheduler.cleanup['check_entities']))
        self.assertEqual(0, len(scheduler.cleanup['alert_entities']))

        # Test cleanup without checks/alerts. If we ran the cleanup task without any checks or alerts, workers would
        # remove everything from redis (PF-3399)
        scheduler.check_definitions = {}
        scheduler.alert_definitions = {}
        scheduler.check_alert_map = {}
        scheduler.app = Mock()
        task = Mock()
        scheduler.app.signature.return_value = task
        scheduler._run_cleanup()
        self.assertFalse(task.apply_async.called, 'Cleanup task shouldn not be scheduled without checks and alerts')


if __name__ == '__main__':
    unittest.main()
