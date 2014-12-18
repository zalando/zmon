#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import sys
import urllib
import urlparse

from zmon_worker.errors import HttpError
from requests.adapters import HTTPAdapter


def absolute_http_url(url):
    '''
    >>> absolute_http_url('')
    False

    >>> absolute_http_url('bla:8080/blub')
    False

    >>> absolute_http_url('https://www.zalando.de')
    True
    '''

    return url.startswith('http://') or url.startswith('https://')


class HttpWrapper(object):

    def __init__(
        self,
        url,
        params=None,
        base_url=None,
        timeout=10,
        max_retries=0,
        verify=True,
        headers=None,
    ):

        self.url = (base_url + url if not absolute_http_url(url) else url)
        self.params = params
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify = verify
        self.headers = headers or {}
        self.__r = None

    def __request(self, raise_error=True):
        if self.__r is not None:
            return self.__r
        if self.max_retries:
            s = requests.Session()
            s.mount('', HTTPAdapter(max_retries=self.max_retries))
        else:
            s = requests

        base_url = self.url
        basic_auth = None

        url_parsed = urlparse.urlsplit(base_url)
        if url_parsed and url_parsed.username and url_parsed.password:
            base_url = base_url.replace("{0}:{1}@".format(urllib.quote(url_parsed.username), urllib.quote(url_parsed.password)), "")
            base_url = base_url.replace("{0}:{1}@".format(url_parsed.username, url_parsed.password), "")
            basic_auth = requests.auth.HTTPBasicAuth(url_parsed.username, url_parsed.password)

        try:
            self.__r = s.get(base_url, params=self.params, timeout=self.timeout, verify=self.verify,
                             headers=self.headers, auth = basic_auth)
        except requests.Timeout, e:
            raise HttpError('timeout', self.url), None, sys.exc_info()[2]
        except requests.ConnectionError, e:
            raise HttpError('connection failed', self.url), None, sys.exc_info()[2]
        except Exception, e:
            raise HttpError(str(e), self.url), None, sys.exc_info()[2]
        if raise_error:
            try:
                self.__r.raise_for_status()
            except requests.HTTPError, e:
                raise HttpError(str(e), self.url), None, sys.exc_info()[2]
        return self.__r

    def json(self, raise_error=True):
        r = self.__request(raise_error=raise_error)
        try:
            return r.json()
        except Exception, e:
            raise HttpError(str(e), self.url), None, sys.exc_info()[2]

    def text(self, raise_error=True):
        r = self.__request(raise_error=raise_error)
        return r.text

    def headers(self, raise_error=True):
        return self.__request(raise_error=raise_error).headers

    def cookies(self, raise_error=True):
        return self.__request(raise_error=raise_error).cookies

    def content_size(self, raise_error=True):
        return len(self.__request(raise_error=raise_error).content)

    def time(self, raise_error=True):
        return self.__request(raise_error=raise_error).elapsed.total_seconds()

    def code(self):
        return self.__request(raise_error=False).status_code


if __name__ == '__main__':
    http = HttpWrapper(sys.argv[1], max_retries=3)
    print http.text()
