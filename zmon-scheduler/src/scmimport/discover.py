#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
ZMON 2.0 check definition discovery script.
Only GIT DeployCtl projects will be scanned for "zmon-checks" folders.
All YAML files in these zmon-checks folders will be imported into the ZMON database.
'''

from argparse import ArgumentParser
from collections import defaultdict
from dogpile.cache import make_region
from fileimport import get_soap_client, import_from_stream, MalformedCheckDefinitionError
from scmmanager import StashApi

import deployctl.client
import eventlog
import json
import logging
import os
import yaml

EVENTS = {'CHECK_DEFINITION_IMPORT_FAILED': eventlog.Event(0x34201, ['checkName', 'owningTeam', 'source', 'reason'])}

DEFAULT_LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s: %(message)s'

memory_cache = make_region().configure('dogpile.cache.memory')


def get_author_info(commits):
    '''
    Gets the name and email of last author from Stash commits

    >>> get_author_info([])
    ('zmon-import', 'undefined')

    >>> get_author_info([{}])
    ('zmon-import', 'undefined')

    >>> get_author_info([{'author': {'name': 'test_dev', 'emailAddress': 'test@zalando.de'}}])
    ('test_dev', 'test@zalando.de')
    '''

    try:
        return commits[0]['author']['name'], commits[0]['author']['emailAddress']
    except:
        return 'zmon-import', 'undefined'


def was_already_imported(source_url, seen_commits, last_commit):
    '''
    >>> was_already_imported('source', set(), [{'id': 'last'}])
    False
    >>> was_already_imported('source', set(['different@commit']), [{'id': 'last'}])
    False
    >>> was_already_imported('source', set(['source@last']), [{'id': 'last'}])
    True
    '''

    if last_commit:
        key = '{}@{}'.format(source_url, last_commit[0]['id'])
        if key in seen_commits:
            return True
    return False


def save_seen_commits(path, seen_commits):
    # remember list of seen commit IDs to not import the same commit twice
    with open(path, 'wb') as fd:
        json.dump(list(seen_commits), fd)


def load_seen_commits(path):
    if os.path.exists(path):
        with open(path) as fd:
            seen_commits = set(json.load(fd))
        return seen_commits
    else:
        return set()


def import_check(soap_client, check, dry_run, logger):
    if dry_run:
        logger.debug('** DRY-RUN ** Would import %s for %s, by: %s', check['source'], check['team'], check['author'])
    else:
        try:
            import_from_stream(soap_client, check['data'], check['source'], check['team'], check['author'])
        except MalformedCheckDefinitionError, e:
            logger.warn('Failed to import %s. %s', check['source'], e.reason)
            eventlog.log(EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName=check['data'].get('name'),
                         owningTeam=check['team'], source=check['source'], reason=e.reason)
        except Exception:
            logger.exception('Failed to import %s', check['source'])
            eventlog.log(EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName=check['data'].get('name'),
                         owningTeam=check['team'], source=check['source'], reason='Exception from import module')


class Project(object):

    def __init__(self, deployctl_project, stash, existing_checks):
        url_parts = deployctl_project.scm_url.split('/')
        project_key = url_parts[4]

        self.name = deployctl_project.name
        self.team = deployctl_project.get_team()
        self.scm_url = deployctl_project.scm_url
        self.repository_name = (url_parts[5])[:-4]
        self.path = '/'.join(url_parts[6:])
        self.stash = stash
        self.existing_checks = existing_checks

        self.repositories = [r for r in self._get_repositories(project_key) if r['name'] == self.repository_name]

        self.existing_checks_by_source, self.existing_checks_by_id = self._get_matching_checks()
        self.stash_checks_by_source = {}
        self.stash_checks_by_id = defaultdict(list)

        self.repositories_scanned = 0
        self.files_scanned = 0
        self.exception_count = 0

        self.logger = logging.getLogger('zmon-import')
        self.logger.info('Got %s existing checks for project %s', len(self.existing_checks_by_source), project_key)

    @memory_cache.cache_on_arguments(namespace='zmon-import')
    def _get_repositories(self, project_key):
        return self.stash.get_repos(project_key)

    def _get_matching_checks(self):
        required = ['sourceUrl', 'name', 'owningTeam']
        by_source = {}
        by_team_and_name = {}
        for check in self.existing_checks:
            if all(hasattr(check, r) for r in required):
                source = str(check.sourceUrl).strip().lower()
                c = {
                    'name': check.name,
                    'source': source,
                    'team': check.owningTeam,
                    'imported': False,
                }
                by_source[source] = c
                by_team_and_name[u'{}:{}'.format(check.owningTeam, check.name)] = c
        return by_source, by_team_and_name

    def _scan_files(self, repo, check_path, files, seen_commits):
        for fpath in files:
            file_path = os.path.join(check_path, fpath)
            source_url = '{}/{}'.format('/'.join(self.scm_url.split('/')[:6]), file_path).strip().lower()
            last_commit = self.stash.get_commits(repo, path=file_path, start=0, limit=1)

            if was_already_imported(source_url, seen_commits, last_commit):
                self.logger.info('The last commit for %s was already imported', source_url)
                if source_url in self.existing_checks_by_source:
                    key = u'{}:{}'.format(self.team, self.existing_checks_by_source[source_url]['name'])
                    check = {'name': self.existing_checks_by_source[source_url]['name'], 'source': source_url,
                             'team': self.team}
                    self.stash_checks_by_source[source_url] = check
                    self.stash_checks_by_id[key].append(check)
                else:
                    self.logger.warn('The last commit for %s is in the cache file, but the check is not in the DB!',
                                     source_url)
            else:
                try:
                    fd = self.stash.get_content(repo, file_path)
                except Exception:
                    # If getting file's content throws an exception and the file was already imported, we
                    # don't want to remove it.
                    self.exception_count += 1
                    self.logger.exception('Error while loading check content from Stash. Repo: %s, path: %s', repo,
                                          file_path)
                    eventlog.log(EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='Unknown',
                                 owningTeam=self.team, source=source_url, reason='Failed to get file content from Stash'
                                 )
                else:
                    seen_commits.add('{}@{}'.format(source_url, last_commit[0]['id']))
                    try:
                        check = yaml.safe_load(fd)
                    except Exception:
                        self.exception_count += 1
                        self.logger.exception('Error while parsing yaml file. Repo: %s, path %s', repo, file_path)
                        eventlog.log(EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName='Unknown',
                                     owningTeam=self.team, source=source_url, reason='Failed to parse yaml file')
                    else:
                        author, email = get_author_info(last_commit)
                        key = u'{}:{}'.format(self.team, check.get('name'))
                        check = {
                            'author': author,
                            'commit': last_commit[0]['id'],
                            'data': check,
                            'email': email,
                            'name': check.get('name'),
                            'source': source_url,
                            'team': self.team,
                        }
                        self.stash_checks_by_source[source_url] = check
                        self.stash_checks_by_id[key].append(check)

    def scan_repositories(self, seen_commits):
        for repo in self.repositories:
            self.repositories_scanned += 1
            self.logger.info('Scanning for check definitions in %s (%s by %s)..', self.repository_name, self.name,
                             self.team)
            check_path = os.path.join(self.path, 'zmon-checks')
            check_definition_files = [f for f in self.stash.get_files(repo, check_path) if f.endswith('.yaml')]
            self.files_scanned += len(check_definition_files)
            self._scan_files(repo, check_path, check_definition_files, seen_commits)

        # If someone changes permissions in Stash, we might lose access to checks directory. In this case, we don't
        # want to delete checks that we imported before, but were unable to read now.
        if not (self.files_scanned > 0 and self.repositories_scanned > 0):
            for key in self.existing_checks_by_source:
                self.existing_checks_by_source[key]['imported'] = True


def main(args):
    logger = logging.getLogger('zmon-import')
    logger.setLevel(level=args.loglevel or logging.INFO)
    if args.log_file:
        file_handler = logging.handlers.TimedRotatingFileHandler(args.log_file, when='midnight')
        file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(file_handler)
    else:
        logger.addHandler(logging.StreamHandler())

    logger.info('Starting check definition discovery')

    # disable verbose logging from "requests" module:
    logging.getLogger('requests').setLevel(logging.WARN)
    soap_client = get_soap_client(args.wsdl_url)
    eventlog.register_all(EVENTS, path=args.eventlog_path)

    seen_commits = load_seen_commits(args.cache_file)
    total_exception_count = 0
    total_repos_scanned = 0

    # We can't split all existing checks by source and id here. We have to pass the list to projects because it's
    # possible to run the script for a single project or list of projects. In this case, all checks for projects not
    # included in the run would be deleted.
    existing_checks_by_source = {}
    existing_checks_by_id = {}
    stash_checks_by_source = {}
    stash_checks_by_id = defaultdict(list)
    existing_checks = defaultdict(list)

    try:
        snapshot_id, ws_checks = soap_client.service.getAllCheckDefinitions()
    except Exception:
        logger.error('Failed to get existing check definitions from ZMON webservice', exc_info=True)
    else:
        # SOAP client wraps checks definitions in a tuple...
        for check in ws_checks[1]:
            if hasattr(check, 'sourceUrl') and check.sourceUrl is not None and check.status != 'DELETED':
                s = str(check.sourceUrl).strip().lower()
                existing_checks[s[:s.rfind('zmon-checks')]].append(check)

        client = deployctl.client.DeployCtl()
        stash = StashApi()

        # We hash existing checks by project's source url. This list comprehension is so long because source url from
        # deploy control sometimes ends with '/' and sometimes it doesn't. To make sure that hashing works, we have to
        # be consistent.
        projects = [Project(p, stash, existing_checks[(p.scm_url if p.scm_url.endswith('/') else p.scm_url + '/')])
                    for p in client.get_projects(scm_url='.git/', name=args.project or '',
                    organization='Zalando/Technology')]
        logger.info('Processing %s projects..', len(projects))

        for project in projects:
            project.scan_repositories(seen_commits)

            existing_checks_by_source.update(project.existing_checks_by_source)
            existing_checks_by_id.update(project.existing_checks_by_id)
            stash_checks_by_source.update(project.stash_checks_by_source)
            for key, checks in project.stash_checks_by_id.iteritems():
                stash_checks_by_id[key].extend(checks)

            total_exception_count += project.exception_count
            total_repos_scanned += project.repositories_scanned

        for key, checks in stash_checks_by_id.iteritems():
            if len(checks) > 1:
                for check in checks:
                    eventlog.log(EVENTS['CHECK_DEFINITION_IMPORT_FAILED'].id, checkName=check['name'],
                                 owningTeam=check['team'], source=check['source'],
                                 reason='Unique constraint violation: check name - team')
                    # If the check was already imported and someone added a duplicate, we mark the existing check as
                    # imported to avoid deleting it. If new check is a duplicate, we remove it from cache to make
                    # sure we're able to discover it again, once someone fixes the conflict.
                    if check['source'] in existing_checks_by_source:
                        existing_checks_by_source[check['source']]['imported'] = True
                    else:
                        seen_commits.discard('{}@{}'.format(check['source'], check['commit']))
            else:
                check = checks[0]
                # TODO We have to store both, seen checks that weren't loaded and new checks that should be loaded. The
                # only difference for now is that new checks have 'data' key. We should refactor it to use a check
                # class with a method that will distinguish between loaded and new checks.
                if 'data' in check:
                    import_check(soap_client, check, args.dry_run, logger)
                if key in existing_checks_by_id:
                    existing_checks_by_id[key]['imported'] = True
                elif check['source'] in existing_checks_by_source:
                    existing_checks_by_source[check['source']]['imported'] = True

        # Deleted. This approach is a bit naive. Currently, I don't have a better idea to ensure that we got a list of
        # projects from DeployCtl and that we actually traversed some repos in Stash. StashApi catches most of the
        # exceptions internally and returns empty lists.
        if projects and total_repos_scanned and total_exception_count == 0:
            for check in (v for (k, v) in existing_checks_by_source.iteritems() if not v['imported']):
                if args.dry_run:
                    logger.debug('** DRY-RUN ** Would delete %s for %s by: %s', check['name'], check['team'],
                                 check['author'])
                else:
                    soap_client.service.deleteCheckDefinition(check['name'], check['team'])
        else:
            logger.warn('Skipping deleting checks due to errors. Projects: %s, repos: %s, exceptions: %s',
                        len(projects), total_repos_scanned, total_exception_count)

        if not args.dry_run:
            save_seen_commits(args.cache_file, seen_commits)

    logger.info('Check definition discovery finished')


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', help='Verbose (debug) logging', action='store_const', const=logging.DEBUG,
                       dest='loglevel')
    group.add_argument('-q', '--quiet', help='Silent mode, only log warnings', action='store_const',
                       const=logging.WARN, dest='loglevel')
    parser.add_argument('--dry-run', help='Noop, do not write anything', action='store_true')
    parser.add_argument('--project', help='Only process a single project')
    parser.add_argument('--cache-file', help='Cache file for Stash commit IDs', default='/tmp/zmon-discover.cache')
    parser.add_argument('--eventlog-path', help='Path to eventlog file', required=True)
    parser.add_argument('--log-file', help='Path to log file')
    parser.add_argument('wsdl_url', help='WSDL url of ZMON 2.0 WS')
    args = parser.parse_args()

    args = parser.parse_args()
    main(args)
