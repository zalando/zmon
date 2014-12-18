#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import re
import sys

from zmon_worker.errors import CheckError, InsufficientPermissionsError, DbError
from psycopg2.extras import NamedTupleCursor

DEFAULT_PORT = 5432

CONNECTION_RE = \
    re.compile(r'''
^(?P<host>[^:/]+)       # host - either IP o hostname
(:(?P<port>\d+))?       # port - integer, optional
/(?P<dbname>\w+)        # database name
$
'''
               , re.X)

ABSOLUTE_MAX_RESULTS = 1000000

REQUIRED_GROUP = 'zalandos'
PERMISSIONS_STMT = \
    '''
SELECT r.rolcanlogin AS can_login,
       ARRAY(SELECT b.rolname
               FROM pg_catalog.pg_auth_members m
               JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
              WHERE m.member = r.oid) AS member_of
  FROM pg_catalog.pg_roles r
 WHERE r.rolname = %s;
'''

NON_SAFE_CHARS = re.compile(r'[^a-zA-Z_0-9-]')


def make_safe(s):
    '''
    >>> make_safe('Bad bad \\' 123')
    'Badbad123'
    '''

    if not s:
        return ''
    return NON_SAFE_CHARS.sub('', s)


class SqlWrapper(object):

    '''Shard-aware SQL adapter
    sql().execute('SELECT 1').result()
    '''

    def __init__(
        self,
        shards,
        user='nagios',
        password='',
        timeout=60000,
        shard=None,
        created_by=None,
        check_id=None,
    ):
        '''
        Parameters
        ----------
        shards: dict
            A dict of shard definitions where key is the shard's name and value is the host/database string.
        user: str
        password: str
        timeout: int
            Statement timeout in milliseconds.
        shard: str
            Optional shard name. If provided, the check will be run on only one shard matching given name.
        created_by: str
            Optional user name. If provided, the check will first make sure that the user has permissions to access the
            requested database. It's optional because it's currently supported only in trial run.
        check_id: int
            The check definition ID in order to set PostgreSQL application name (easier tracking on server side).
        '''

        if not shards:
            raise CheckError('SqlWrapper: No shards defined')
        if shard and not shards.get(shard):
            raise CheckError('SqlWrapper: Shard {} not found in shards definition'.format(shard))

        self._cursors = []
        self._stmt = None
        permissions = {}

        for shard_def in ([shards[shard]] if shard else shards.values()):
            m = CONNECTION_RE.match(shard_def)
            if not m:
                raise CheckError('Invalid shard connection: {}'.format(shard_def))
            connection_str = \
                "host='{host}' port='{port}' dbname='{dbname}' user='{user}' password='{password}' options='-c statement_timeout={timeout}' application_name='ZMON Check {check_id} (created by {created_by})' ".format(
                host=m.group('host'),
                port=int(m.group('port') or DEFAULT_PORT),
                dbname=m.group('dbname'),
                user=user,
                password=password,
                timeout=timeout,
                check_id=check_id,
                created_by=make_safe(created_by),
            )
            try:
                conn = psycopg2.connect(connection_str)
                conn.set_session(readonly=True, autocommit=True)
                cursor = conn.cursor(cursor_factory=NamedTupleCursor)
                self._cursors.append(cursor)
            except Exception, e:
                raise DbError(str(e), operation='Connect to {}'.format(shard_def)), None, sys.exc_info()[2]
            try:
                if created_by:
                    cursor.execute(PERMISSIONS_STMT, [created_by])
                    row = cursor.fetchone()
                    permissions[shard_def] = (row.can_login and REQUIRED_GROUP in row.member_of if row else False)
            except Exception, e:
                raise DbError(str(e), operation='Permission query'), None, sys.exc_info()[2]

        for resource, permitted in permissions.iteritems():
            if not permitted:
                raise InsufficientPermissionsError(created_by, resource)

    def execute(self, stmt):
        self._stmt = stmt
        return self

    def result(self, agg=sum):
        '''return single row result, will result primitive value if only one column is selected'''

        result = {}
        try:
            for cur in self._cursors:
                try:
                    cur.execute(self._stmt)
                    row = cur.fetchone()
                    if row:
                        for k, v in row._asdict().items():
                            result[k] = result.get(k, [])
                            result[k].append(v)
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self._stmt), None, sys.exc_info()[2]

        for k, v in result.items():
            try:
                result[k] = agg(v)
            except:
                # just use list if aggregation function fails
                # (e.g. if we try to sum strings)
                result[k] = v
        if len(result) == 1:
            return result.values()[0]
        else:
            return result

    def results(self, max_results=100, raise_if_limit_exceeded=True):
        '''return many rows'''

        results = []
        max_results = min(max_results, ABSOLUTE_MAX_RESULTS)
        try:
            for cur in self._cursors:
                try:
                    cur.execute(self._stmt)
                    if raise_if_limit_exceeded:
                        rows = cur.fetchmany(max_results + 1)
                        if len(rows) > max_results:
                            raise DbError('Too many results, result set was limited to {}. Try setting max_results to a higher value.'.format(max_results),
                                          operation=self._stmt)
                    else:
                        rows = cur.fetchmany(max_results)
                    for row in rows:
                        results.append(row._asdict())
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self._stmt), None, sys.exc_info()[2]
        return results


if __name__ == '__main__':
    if len(sys.argv) == 4:
        check = SqlWrapper([sys.argv[1] + '/' + sys.argv[2]])
        print check.execute(sys.argv[3]).result()
    elif len(sys.argv) > 1:
        print 'sql.py <host> <dbname> <stmt>'
