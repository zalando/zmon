#!/usr/bin/env python
# -*- coding: utf-8 -*-

import eventlog
import logging
import unittest
import yaml

from deployctl.client import Project, DeployCtl
from mock import call, patch, MagicMock, PropertyMock, ANY
from scmimport import discover
from scmmanager import StashApi


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


def mock_two_projects(self, *args, **kwargs):
    return [Project({
        'group': 'de.zalando',
        'description': 'Article Team System Checks for ZMON 2.0',
        'parent': None,
        'title': 'ZMON Checks Article',
        'scm_url': 'https://scm.example.org/scm/article/zmon-checks.git/',
        'deployable': False,
        'deployment_set_name': None,
        'version': '1.0',
        'organization': 'Backend/Article',
        'has_database': False,
        'type': 'zmon-checks',
        'name': 'zmon-checks-article',
    }), Project({
        'group': 'de.zalando',
        'description': 'The service is the deploy unit for the catalog repository.',
        'parent': ['de.zalando.catalog', 'catalog-parent', '1.2.84'],
        'title': 'Catalog Repository Service',
        'scm_url': 'https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service',
        'deployable': True,
        'deployment_set_name': 'catalog',
        'version': 'master-SNAPSHOT',
        'organization': 'Zalando/Technology/Backend/Article',
        'has_database': True,
        'type': 'maven-war',
        'name': 'catalog-service',
    })]


def mock_two_repos(self, proj_key):
    return [{
        'cloneUrl': 'https://git@scm.example.org/scm/article/zmon-checks.git',
        'forkable': True,
        'id': 701,
        'link': {'rel': 'self', 'url': '/projects/ARTICLE/repos/zmon-checks/browse'},
        'name': 'zmon-checks',
        'project': {
            'id': 24,
            'isPersonal': False,
            'key': 'ARTICLE',
            'link': {'rel': 'self', 'url': '/projects/ARTICLE'},
            'name': 'Backend/Article',
            'public': False,
            'type': 'NORMAL',
        },
        'public': False,
        'scmId': 'git',
        'slug': 'zmon-checks',
        'state': 'AVAILABLE',
        'statusMessage': 'Available',
    }, {
        'cloneUrl': 'https://git@scm.example.org/scm/article/zeos-catalog.git',
        'forkable': True,
        'id': 300,
        'link': {'rel': 'self', 'url': '/projects/ARTICLE/repos/zeos-catalog/browse'},
        'name': 'zeos-catalog',
        'project': {
            'id': 24,
            'isPersonal': False,
            'key': 'ARTICLE',
            'link': {'rel': 'self', 'url': '/projects/ARTICLE'},
            'name': 'Backend/Article',
            'public': False,
            'type': 'NORMAL',
        },
        'public': False,
        'scmId': 'git',
        'slug': 'zeos-catalog',
        'state': 'AVAILABLE',
        'statusMessage': 'Available',
    }]


def mock_two_repos_files(self, repo, check_path):
    return (['old.yaml'] if repo['slug'] == 'zeos-catalog' else ['new.yaml'])


def mock_two_repos_content(self, repo, file_path):
    return ('old' if repo['slug'] == 'zeos-catalog' else 'new')


def mock_two_repos_yaml(fd):
    return {'team': 'article', 'name': 'check'}


def mock_two_repos_existing_checks():
    snapshot_id = 0
    checks = \
        [{'sourceUrl': 'https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service/zmon-checks/old.yaml'
         , 'name': 'check', 'owningTeam': 'Backend/Article'}]

    mocks = []
    for c in checks:
        m = MagicMock()
        for k, v in c.iteritems():
            p = PropertyMock(return_value=v)
            setattr(type(m), k, p)
        mocks.append(m)

    return snapshot_id, ('checkDefinitions', mocks)


class TestImport(unittest.TestCase):

    @patch.object(DeployCtl, 'get_projects', mock_two_projects)
    @patch.object(StashApi, 'get_repos', mock_two_repos)
    @patch.object(StashApi, 'get_files', mock_two_repos_files)
    @patch.object(StashApi, 'get_commits', mock_commits)
    @patch.object(StashApi, 'get_content', mock_two_repos_content)
    @patch.object(yaml, 'safe_load', mock_two_repos_yaml)
    @patch.object(eventlog, 'register_all', lambda *args, **kwargs: True)
    @patch.object(eventlog, 'log')
    @patch.object(discover, 'get_soap_client')
    @patch.object(discover, 'import_from_stream')
    @patch.object(discover, 'load_seen_commits')
    @patch.object(discover, 'save_seen_commits')
    def test_move_between_repos(self, mock_save, mock_load, mock_import, mock_soap, mock_eventlog):
        '''
        If the same check is recreated in new repository, imported, then deleted in the old one, the discovery script
        should update the check without calling the delete.
        '''

        args = MagicMock()
        args.loglevel = logging.CRITICAL
        args.log_file = None
        args.cache_file = 'no_cache'
        args.wsdl_url = 'wsdl_url'
        args.dry_run = False
        soap_service = MagicMock()
        soap_service.service.deleteCheckDefinition.return_value = True
        soap_service.service.getAllCheckDefinitions.return_value = mock_two_repos_existing_checks()
        mock_soap.return_value = soap_service
        mock_load.return_value = \
            set(['https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service/zmon-checks/old.yaml@4fac31a7d9a24fdd3ebc4bd01d4b84e875ef0b7a'
                ])
        mock_save.return_value = True

        discover.main(args)

        eventlog_calls = [call(discover.EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='check',
                          owningTeam='Backend/Article',
                          source='https://scm.example.org/scm/article/zmon-checks.git/zmon-checks/new.yaml',
                          reason='Unique constraint violation: check name - team'),
                          call(discover.EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='check',
                          owningTeam='Backend/Article',
                          source='https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service/zmon-checks/old.yaml'
                          , reason='Unique constraint violation: check name - team')]

        self.assertFalse(mock_import.called)
        self.assertFalse(soap_service.service.deleteCheckDefinition.called)
        mock_save.assert_called_once_with(args.cache_file,
                                          set(['https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service/zmon-checks/old.yaml@4fac31a7d9a24fdd3ebc4bd01d4b84e875ef0b7a'
                                          ]))
        mock_eventlog.assert_has_calls(eventlog_calls, any_order=True)

        # Now remove the old check and test if update is called with the new one.
        def mock_deleted_files(self, repo, check_path):
            return ([] if repo['slug'] == 'zeos-catalog' else ['new.yaml'])

        StashApi.get_files = mock_deleted_files
        mock_eventlog.reset_mock()
        mock_save.reset_mock()

        discover.main(args)

        mock_import.assert_called_once_with(ANY, ANY,
                                            'https://scm.example.org/scm/article/zmon-checks.git/zmon-checks/new.yaml'
                                            , 'Backend/Article', 'Test Dev')
        self.assertFalse(soap_service.service.deleteCheckDefinition.called)
        mock_save.assert_called_once_with(args.cache_file,
                                          set(['https://scm.example.org/scm/article/zeos-catalog.git/catalog-service/service/zmon-checks/old.yaml@4fac31a7d9a24fdd3ebc4bd01d4b84e875ef0b7a'
                                          ,
                                          'https://scm.example.org/scm/article/zmon-checks.git/zmon-checks/new.yaml@4fac31a7d9a24fdd3ebc4bd01d4b84e875ef0b7a'
                                          ]))
        self.assertFalse(mock_eventlog.called)


if __name__ == '__main__':
    unittest.main()
