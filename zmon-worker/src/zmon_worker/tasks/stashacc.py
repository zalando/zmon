#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from scmmanager import StashApi
except:
    StashApi = None
import os
import yaml
import logging


class StashAccessor(object):

    def __init__(self, logger=None):
        self._logger = (logger if logger else _get_null_logger())
        if StashApi:
            self.stash = StashApi()
        else:
            self.stash = None

    def set_logger(self, logger):
        self._logger = logger

    def get_stash_check_definitions(self, *repo_urls):
        '''
        Downloads the check definitions found under the given stash repositories.
        Returns a list of dict corresponding to the check definitions
        '''

        check_definitions = []
        if self.stash:
            for repo_url in repo_urls:
                try:
                    repo, check_path = self.stash.get_repo_from_scm_url(repo_url)
                except Exception:
                    self._logger.exception('Bad configured stash repo: %s. Exception follows: ', repo_url)
                else:
                    try:
                        files = [f for f in self.stash.get_files(repo, check_path) if f.endswith('.yaml')]
                        if not files:
                            self._logger.warn('No check definitions found in secure repo: %s', repo_url)

                        for check_file in files:
                            file_path = os.path.join(check_path, check_file)
                            fd = self.stash.get_content(repo, file_path)
                            check_definitions.append(yaml.safe_load(fd))
                    except Exception:
                        self._logger.exception('Unexpected error when fetching info from stash: ')
            if repo_urls and not check_definitions:  # StashApi returns empty results on failure
                self._logger.error('Stash error: Check definition download finished with empty results')
                raise Exception('Check definition download finished with empty results')

        return check_definitions

    def get_stash_commands(self, *repo_urls):
        '''
        Returns a list of str corresponding to commands found in check_definitions under the given stash repositories
        '''

        return set(cf['command'] for cf in self.get_stash_check_definitions(*repo_urls) if 'command' in cf)


class NullHandler(logging.Handler):

    def emit(self, record):
        pass


_null_logger = None


def _get_null_logger():
    global _null_logger
    if not _null_logger:
        handler = NullHandler()
        _null_logger = logging.getLogger('NullLogger')
        _null_logger.addHandler(handler)
    return _null_logger


