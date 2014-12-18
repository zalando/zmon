#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import ldap
try:
    import ldapapi
except:
    ldapapi = None
import logging
import time

from counter import CounterWrapper
from zmon_worker.errors import CheckError
from functools import partial
from ldap.dn import explode_dn

STATISTICS_OPERATIONS_TO_MONITOR = frozenset([
    'bind',
    'unbind',
    'search',
    'modify',
    'add',
    'delete',
    'extended',
])

STATISTICS_GAUGE_KEYS = frozenset([
    'threads_active',
    'threads_max',
    'connections_current',
    'statistics_entries',
    'waiters_read',
    'waiters_write',
    'connections_max_file_descriptors',
])

# rename some keys to make the names more friendly
STATISTICS_FRIENDLY_KEY_NAMES = {'statistics_entries': 'entries',
                                 'connections_max_file_descriptors': 'max_file_descriptors'}


class UnsupportedMethodException(Exception):

    pass


class DuplicateBindException(Exception):

    pass


class LdapWrapper(object):

    def __init__(
        self,
        host=None,
        tls=True,
        krb5=False,
        user='uid=nagios,ou=robots,ou=users,dc=example,dc=com',
        password='',
        timeout=60,
        logger=None,
        counter=None,
    ):
        '''expects ready to use "partial" for counter (CounterWrapper)'''

        self.logger = logger or logging.getLogger()
        self._counter = counter('')
        self.use_tls = tls
        self.use_krb5 = krb5
        self.user_base_dn = ','.join(explode_dn(user)[1:])
        self.user_filter = '(uid=nagios)'
        self.user_attrib = ['dn']
        # password auth
        self.bind_dn = user
        self.__password = password
        self.session = None
        self.host = host
        if self.host and len(self.host.split('.')) <= 1:
            # FIXME
            self.host += '.zalando'

    def _connect(self, ldapserver):
        if self.session:
            raise CheckError('LDAP Error: duplicate bind exception.')
        self.logger.debug('connect to %s', ldapserver)
        uri = 'ldap://{0}'.format(ldapserver)
        try:
            if self.use_krb5 and self.use_tls:
                self.logger.debug('sasl bind')
                self.session = ldapapi.Session(uri, tls=True)
            elif self.use_tls:
                self.logger.debug('simple bind')
                self.session = ldapapi.Session(uri, self.bind_dn, self.__password, tls=True)
            else:
                raise CheckError('LDAP Error: unsupported method exception.')
        except CheckError:
            raise
        except Exception, e:
            raise CheckError('Error connecting to LDAP: {}'.format(e)), None, sys.exc_info()[2]

    def _search(self, base, fltr, attrs, scope=ldap.SCOPE_SUBTREE):
        return self.session.search(base, fltr, attrs, scope)

    def _disconnect(self):
        self.logger.debug('disconnect')
        try:
            self.session.disconnect()
        except Exception, e:
            raise CheckError('Error disconnecting to LDAP: {}'.format(e)), None, sys.exc_info()[2]
        self.session = None

    def _sync_state(self, ldapserver):
        base = 'dc=example,dc=com'
        fltr = '(objectclass=*)'
        attr = ['contextCSN']
        self._connect(ldapserver)
        result = self._search(base, fltr, attr, scope=ldap.SCOPE_BASE)
        self._disconnect()
        return result[0][1]['contextCSN']

    def _get_rid_to_url(self, ldapserver):
        '''Returns a dict for this query:
        % ldapsearch -b cn=config '(cn=config)' -H ldap://myserver olcServerID
        '''

        rid2url = {}
        url2rid = {}
        base = 'cn=config'
        fltr = '(cn=config)'
        attr = ['olcServerID']
        self._connect(ldapserver)
        res = self.session.conn.search_ext_s(base, ldap.SCOPE_BASE, fltr, attr)
        self._disconnect()
        for rid_url in res[0][1]['olcServerID']:
            rid, url = rid_url.split()
            rid = '%03d' % int(rid)
            rid2url[rid] = url
            url2rid[url] = rid
        return rid2url, url2rid

    def _get_timestamp_rid(self, csn):
        '''csn: 20140227093429.363252Z#000000#004#000000'''

        ts, _, rid, _ = csn.split('#')
        ts = ts.split('.')[0]
        # ts = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S")
        ts = int(ts)
        return rid, ts

    def sync(self):
        '''Example:
        checkldap().sync() => [{'newest': 20140516151002, 'elapsed': 0.14442706108093262, 'ok': True, 'diff': 0, 'server': 'myserv'}, {'newest': 20140516151002, 'elapsed': 0.19423580169677734, 'ok': True, 'diff': 0, 'server': 'myserver'}, {'newest': 20140516151002, 'elapsed': 0.2617530822753906, 'ok': True, 'diff': 0, 'server': 'z-auth123.example'}, {'newest': 20140516151002, 'elapsed': 0.15635299682617188, 'ok': True, 'diff': 0, 'server': 'myserver'}, {'newest': 20140516151002, 'elapsed': 0.20283913612365723, 'ok': True, 'diff': 0, 'server': 'myserver'}]
        '''

        try:
            rid2url, url2rid = self._get_rid_to_url(self.host)
            ldapservers = map(lambda url: url[7:], url2rid.keys())
            return self._sync(ldapservers)
        except CheckError:
            raise
        except Exception, e:
            raise CheckError('{}'.format(e)), None, sys.exc_info()[2]

    def _sync(self, ldapservers):
        '''Returns a list of dict, where 'diff' is the difference to the 'newest' of the full list, 'newest' is the newest timestamp for the given 'server', 'ok' means LDAP state for current 'server' and 'elapsed' the runtime of that ldap request.
        Example dict:
        {'diff': 0,
        'elapsed': 0.2969970703125,
        'newest': 20140228135148,
        'ok': True,
        'server': 'myserver'}
        '''

        if not ldapservers:
            return
        results = []
        for ldapserver in ldapservers:
            try:
                start = time.time()
                csn_list = self._sync_state(ldapserver)
                rid2ts = {}
                rid_ts = map(lambda csn: self._get_timestamp_rid(csn), csn_list)
                newest = rid_ts[0][1]
                for rid, ts in rid_ts:
                    rid2ts[rid] = ts
                    if ts > newest:
                        newest = ts
                elapsed = time.time() - start
                results.append({
                    'server': ldapserver,
                    'ok': True,
                    'newest': newest,
                    'elapsed': elapsed,
                })
            except ldap.LOCAL_ERROR:
                bind_type = 'simple bind'
                if self.use_krb5:
                    bind_type = 'sasl bind'
                msg = 'Could not connect to {} via {}'.format(ldapserver, bind_type)
                self.logger.exception(msg)
                raise CheckError(msg)
            except ldap.CONFIDENTIALITY_REQUIRED:
                results.append({'ok': False, 'server': ldapserver})
        newest = 0
        for result in results:
            if result['ok']:
                if result['newest'] > newest:
                    newest = result['newest']
        for result in results:
            if result['ok']:
                result['diff'] = newest - result['newest']
        return results

    def auth(self):
        try:
            start = time.time()
            self._connect(self.host)
            connect_elapsed = time.time() - start
            self._search(self.user_base_dn, self.user_filter, self.user_attrib)
            all_elapsed = time.time() - start
            search_elapsed = all_elapsed - connect_elapsed
            self._disconnect()
            return {
                'ok': True,
                'connect_time': connect_elapsed,
                'search_time': search_elapsed,
                'elapsed': all_elapsed,
            }
        except ldap.LOCAL_ERROR:
            bind_type = 'simple bind'
            if self.use_krb5:
                bind_type = 'sasl bind'
            msg = 'Could not connect to {} via {}'.format(self.host, bind_type)
            self.logger.exception(msg)
            raise CheckError(msg)
        except ldap.CONFIDENTIALITY_REQUIRED:
            return {'ok': False}
        except Exception, e:
            raise CheckError('Error authenticating to LDAP: {}'.format(e)), None, sys.exc_info()[2]

    @staticmethod
    def _split_monitor_dn(dn):
        '''
        >>> LdapWrapper._split_monitor_dn('cn=Max File Descriptors,cn=Connections,cn=Monitor')
        ('connections', 'max_file_descriptors')
        '''

        parts = dn.replace(' ', '_').split(',')
        return (parts[1])[3:].lower(), (parts[0])[3:].lower()

    def statistics_raw(self):
        '''collect statistics from OpenLDAP "Monitor" DB as a dict

        ldapsearch -b cn=Connections,cn=Monitor -H ldap://myserver '(monitorCounter=*)' '+'

        Example result::

            {
              "connections_current": "51",
              "connections_max_file_descriptors": "65536",
              "connections_total": "26291",
              "operations_add_completed": "0",
              "operations_add_initiated": "0",
              "operations_bind_completed": "25423",
              "operations_bind_initiated": "25423",
              "operations_delete_completed": "0",
              "operations_delete_initiated": "0",
              "operations_extended_completed": "293",
              "operations_extended_initiated": "293",
              "operations_modify_completed": "91",
              "operations_modify_initiated": "91",
              "operations_search_completed": "22865",
              "operations_search_initiated": "22866",
              "operations_unbind_completed": "25233",
              "operations_unbind_initiated": "25233",
              "statistics_bytes": "122581936",
              "statistics_entries": "64039",
              "statistics_pdu": "112707",
              "statistics_referrals": "0",
              "waiters_read": "51",
              "waiters_write": "0"
            }
        '''

        try:
            self._connect(self.host)
            data = {}
            # we need to use the internal "conn" attribute as the default _search is using paging which does not work for the "cn=Monitor" tree!
            result = self.session.conn.search_s('cn=Monitor', ldap.SCOPE_SUBTREE, '(objectClass=monitorCounterObject)',
                                                ['monitorCounter'])
            for dn, attr in result:
                category, counter = self._split_monitor_dn(dn)
                data['{}_{}'.format(category, counter)] = int(attr['monitorCounter'][0])

            result = self.session.conn.search_s('cn=Threads,cn=Monitor', ldap.SCOPE_SUBTREE,
                                                '(&(objectClass=monitoredObject)(monitoredInfo=*))', ['monitoredInfo'])
            for dn, attr in result:
                category, key = self._split_monitor_dn(dn)
                if key in ('active', 'max'):
                    data['{}_{}'.format(category, key)] = int(attr['monitoredInfo'][0])

            result = self.session.conn.search_s('cn=Operations,cn=Monitor', ldap.SCOPE_SUBTREE,
                                                '(objectClass=monitorOperation)', ['monitorOpInitiated',
                                                'monitorOpCompleted'])
            for dn, attr in result:
                category, op = self._split_monitor_dn(dn)
                if op in STATISTICS_OPERATIONS_TO_MONITOR:
                    data['{}_{}_initiated'.format(category, op)] = int(attr['monitorOpInitiated'][0])
                    data['{}_{}_completed'.format(category, op)] = int(attr['monitorOpCompleted'][0])
            self._disconnect()
        except CheckError:
            raise
        except Exception, e:
            raise CheckError('{}'.format(e)), None, sys.exc_info()[2]
        return data

    def statistics(self):
        '''uses raw statistics and computes counter values (i.e. e.g. operations per second)

        Example result::

            {
              "connections_current": 74,
              "connections_per_sec": 24.1,
              "entries": 353540,
              "max_file_descriptors": 65536,
              "operations_add_per_sec": 0.0,
              "operations_bind_per_sec": 26.4,
              "operations_delete_per_sec": 0.0,
              "operations_extended_per_sec": 1.15,
              "operations_modify_per_sec": 0.0,
              "operations_search_per_sec": 20.66,
              "operations_unbind_per_sec": 24.1,
              "threads_active": 2,
              "threads_max": 16,
              "waiters_read": 73,
              "waiters_write": 0
            }
        '''

        _data = self.statistics_raw()
        data = {}
        for key, val in _data.items():
            if key in STATISTICS_GAUGE_KEYS:
                data[STATISTICS_FRIENDLY_KEY_NAMES.get(key, key)] = val
            elif key == 'connections_total':
                data['connections_per_sec'] = round(self._counter.key(key).per_second(val), 2)
            elif key.startswith('operations_') and key.endswith('_initiated'):
                data[key.replace('_initiated', '_per_sec')] = round(self._counter.key(key).per_second(val), 2)

        # gc_count = round(self._counter.key('gcCount').per_second(gc_count), 2)
        return data


