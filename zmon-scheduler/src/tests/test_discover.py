#!/usr/bin/env python
# -*- coding: utf-8 -*-

import eventlog
import json
import logging
import os
import unittest
import yaml

from deployctl.client import Project, DeployCtl
from mock import call, patch, MagicMock, PropertyMock, ANY
from scmimport import discover
from scmmanager import StashApi

DIR = os.path.dirname(os.path.abspath(__file__))


def mock_projects(self, *args, **kwargs):
    with open(os.path.join(DIR, 'fixtures', 'projects.json')) as f:
        projects = json.load(f)
    if 'organization' in kwargs:
        del kwargs['organization']
    if 'scm_url' in kwargs:
        del kwargs['scm_url']
    return [Project(p) for p in projects if all(p[k] == v for (k, v) in kwargs.iteritems())]


def mock_repos(self, proj_key):
    return [{
        'cloneUrl': 'https://git@scm.example.org/scm/platform/zmon2-software-checks.git',
        'forkable': True,
        'id': 466,
        'link': {'rel': 'self', 'url': '/projects/PLATFORM/repos/zmon2-software-checks/browse'},
        'name': 'zmon2-software-checks',
        'project': {
            'description': 'Team PF Software',
            'id': 25,
            'isPersonal': False,
            'key': 'PLATFORM',
            'link': {'rel': 'self', 'url': '/projects/PLATFORM'},
            'name': 'Platform/Software',
            'public': False,
            'type': 'NORMAL',
        },
        'public': False,
        'scmId': 'git',
        'slug': 'zmon2-software-checks',
        'state': 'AVAILABLE',
        'statusMessage': 'Available',
    }]


def mock_files(self, repo, check_path):
    return [
        'added.yaml',
        'moved.yaml',
        'modified.yaml',
        'copy.yaml',
        'original.yaml',
        'seen.yaml',
    ]


def mock_commits(self, repo, *args, **kwargs):
    return [{
        'authorTimestamp': 1390494882000,
        'author': {'emailAddress': 'test@zalando.de', 'name': 'Test Dev'},
        'parents': [],
        'displayId': '4fac31a',
        'attributes': {'jira-key': ['PF-2583']},
        'message': 'PF-2583 Test',
        'id': '4fac31a7d9a24fdd3ebc4bd01d4b84e875ef0b7a',
    }]


def mock_existing_checks():
    '''
    This function mocks getAllCheckDefinitions response. The return value is a tuple: snapshot id and a list of
    existing check definitions. Mocking part is a bit different than usual. If we use Mock directly
    (e.g. Mock(**check[0])), it'll create properties as children mocks which will result in wrong dict keys. This is
    why we have to use PropertyMock (http://www.voidspace.org.uk/python/mock/mock.html#mock.PropertyMock). Please note
    that one check definition belongs to a different team/project. In the following tests, this definition should not
    be imported nor deleted.
    '''

    snapshot_id = 0
    checks = [
        {
            'sourceurl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/old-moved.yaml',
            'name': 'moved',
            'owningteam': 'platform/software',
            'status': 'active',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/modified.yaml',
            'name': 'modified',
            'owningTeam': 'Platform/Software',
            'status': 'ACTIVE',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/deleted.yaml',
            'name': 'deleted',
            'owningTeam': 'Platform/Software',
            'status': 'ACTIVE',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/original.yaml',
            'name': 'original',
            'owningTeam': 'Platform/Software',
            'status': 'ACTIVE',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/seen.yaml',
            'name': 'seen',
            'owningTeam': 'Platform/Software',
            'status': 'ACTIVE',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/shop/zmon2-shop-checks.git/zmon-checks/shop.yaml',
            'name': 'other',
            'owningTeam': 'Shop',
            'status': 'ACTIVE',
        },
        {
            'sourceUrl': 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/old-check.yaml',
            'name': 'modified',
            'owningTeam': 'Platform/Software',
            'status': 'DELETED',
        },
    ]

    mocks = []
    for c in checks:
        m = MagicMock()
        for k, v in c.iteritems():
            p = PropertyMock(return_value=v)
            setattr(type(m), k, p)
        mocks.append(m)

    return snapshot_id, ('checkDefinitions', mocks)


def mock_content(self, repo, file_path):
    return file_path


def mock_yaml(fd):
    '''
    In live environment, we get check definitions as file-like objects, which are later parsed as yaml. We want to
    simulate two check definitions with the same name and owning team, but different source url. That's why both,
    original and copy check requests, have the same name: original.
    '''

    results = dict(('zmon-checks/{}'.format(f), {'name': f[0:-5]}) for f in mock_files(0, 'r', 'p')
                   if not f.startswith('copy'))
    results['zmon-checks/copy.yaml'] = {'name': 'original'}
    return results[fd]


class TestDiscover(unittest.TestCase):

    def setUp(self):
        self.args = MagicMock()
        self.args.loglevel = logging.CRITICAL
        self.args.log_file = None
        self.args.cache_file = 'no_cache'
        self.args.wsdl_url = 'wsdl_url'
        self.args.project = 'zmon-software-checks'
        self.args.dry_run = False

    @patch.object(DeployCtl, 'get_projects', mock_projects)
    @patch.object(StashApi, 'get_repos', mock_repos)
    @patch.object(StashApi, 'get_files', mock_files)
    @patch.object(StashApi, 'get_commits', mock_commits)
    @patch.object(StashApi, 'get_content', mock_content)
    @patch.object(yaml, 'safe_load', mock_yaml)
    @patch.object(eventlog, 'register_all', lambda *args, **kwargs: True)
    @patch.object(eventlog, 'log')
    @patch.object(discover, 'get_soap_client')
    @patch.object(discover, 'import_from_stream')
    @patch.object(discover, 'load_seen_commits')
    @patch.object(discover, 'save_seen_commits')
    def test_check_import(self, mock_save, mock_load, mock_import, mock_soap, mock_eventlog):
        scm_url = 'https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/'
        last_commit = mock_commits(self, 'repo')[0]['id']
        soap_service = MagicMock()
        soap_service.service.deleteCheckDefinition.return_value = True
        soap_service.service.getAllCheckDefinitions.return_value = mock_existing_checks()
        mock_soap.return_value = soap_service
        mock_load.return_value = set(['{}seen.yaml@{}'.format(scm_url, last_commit),
                                     '{}old-moved.yaml@{}'.format(scm_url, last_commit)])
        mock_save.return_value = True

        discover.main(self.args)

        # Three checks should be imported, two should be discarded and one should be deleted. Also, one check hasn't
        # changed from when the script was last ran. This check should be present in seen_commits, but should not be
        # imported (seen.yaml).
        import_calls = [call(ANY, ANY, scm_url + 'added.yaml', 'Platform/Software', 'Test Dev'), call(ANY, ANY, scm_url
                        + 'moved.yaml', 'Platform/Software', 'Test Dev'), call(ANY, ANY, scm_url + 'modified.yaml',
                        'Platform/Software', 'Test Dev')]

        seen_commits = [
            '{}{}@{}'.format(scm_url, 'added.yaml', last_commit),
            '{}{}@{}'.format(scm_url, 'moved.yaml', last_commit),
            '{}{}@{}'.format(scm_url, 'modified.yaml', last_commit),
            '{}{}@{}'.format(scm_url, 'original.yaml', last_commit),
            '{}{}@{}'.format(scm_url, 'seen.yaml', last_commit),
            '{}{}@{}'.format(scm_url, 'old-moved.yaml', last_commit),
        ]

        # This is not a typo, both checks have the same name and team, but are in two different locations. This
        # simulates the case when user copies a check and forgets to change the name or team.
        eventlog_calls = [call(discover.EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='original',
                          owningTeam='Platform/Software',
                          source='https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/copy.yaml'
                          , reason='Unique constraint violation: check name - team'),
                          call(discover.EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='original',
                          owningTeam='Platform/Software',
                          source='https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/original.yaml'
                          , reason='Unique constraint violation: check name - team')]

        mock_import.assert_has_calls(import_calls, any_order=True)
        mock_save.assert_called_once_with(self.args.cache_file, set(seen_commits))
        soap_service.service.deleteCheckDefinition.assert_called_once_with('deleted', 'Platform/Software')
        mock_eventlog.assert_has_calls(eventlog_calls, any_order=True)

    @patch.object(DeployCtl, 'get_projects', mock_projects)
    @patch.object(StashApi, 'get_repos', mock_repos)
    @patch.object(StashApi, 'get_files', mock_files)
    @patch.object(StashApi, 'get_commits', mock_commits)
    @patch.object(yaml, 'safe_load', mock_yaml)
    @patch.object(eventlog, 'register_all', lambda *args, **kwargs: True)
    @patch.object(eventlog, 'log', lambda *args, **kwargs: True)
    @patch.object(StashApi, 'get_content', side_effect=IOError)
    @patch.object(discover, 'get_soap_client')
    @patch.object(discover, 'import_from_stream')
    @patch.object(discover, 'load_seen_commits')
    @patch.object(discover, 'save_seen_commits')
    def test_handling_exceptions(self, mock_save, mock_load, mock_import, mock_soap, mock_exception):
        '''
        For given project, if importing check throws an exception, the check should not be imported not deleted.
        '''

        soap_service = MagicMock()
        soap_service.service.deleteCheckDefinition.return_value = True
        soap_service.service.getAllCheckDefinitions.return_value = mock_existing_checks()
        mock_soap.return_value = soap_service
        mock_load.return_value = set()
        mock_save.return_value = True

        discover.main(self.args)

        self.assertFalse(mock_import.called)
        self.assertFalse(soap_service.service.deleteCheckDefinition.called)

    @patch.object(DeployCtl, 'get_projects', mock_projects)
    @patch.object(StashApi, 'get_repos', mock_repos)
    @patch.object(StashApi, 'get_files', lambda *args, **kwargs: [])
    @patch.object(StashApi, 'get_commits', mock_commits)
    @patch.object(yaml, 'safe_load', mock_yaml)
    @patch.object(eventlog, 'register_all', lambda *args, **kwargs: True)
    @patch.object(eventlog, 'log', lambda *args, **kwargs: True)
    @patch.object(StashApi, 'get_content', mock_content)
    @patch.object(discover, 'get_soap_client')
    @patch.object(discover, 'import_from_stream')
    @patch.object(discover, 'load_seen_commits')
    @patch.object(discover, 'save_seen_commits')
    def test_no_stash_access(self, mock_save, mock_load, mock_import, mock_soap):
        '''
        If it happens that we have already imported checks for a project, but during the next run, the script cannot
        access the directory in stash, we shouldn't delete any checks.
        '''

        soap_service = MagicMock()
        soap_service.service.deleteCheckDefinition.return_value = True
        soap_service.service.getAllCheckDefinitions.return_value = mock_existing_checks()
        mock_soap.return_value = soap_service
        mock_load.return_value = set()
        mock_save.return_value = True

        discover.main(self.args)

        self.assertFalse(mock_import.called)
        self.assertFalse(soap_service.service.deleteCheckDefinition.called)


if __name__ == '__main__':
    unittest.main()
