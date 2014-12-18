#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
from zmon_worker.errors import DbError

DEFAULT_PORT = 3306
MAX_RESULTS = 100

CONNECTION_RE = \
    re.compile(r'''
^(?P<host>[^:/]+)       # host - either IP o hostname
(:(?P<port>\d+))?       # port - integer, optional
/(?P<dbname>\w+)        # database name
$
'''
               , re.X)


def _import_db_driver():
    module_alternatives = 'MySQLdb', 'pymysql'
    for module in module_alternatives:
        try:
            return __import__(module, globals(), locals(), [], -1)
        except Exception, e:
            if module == module_alternatives[-1]:
                raise
            else:
                # print is well supported by celery, this will end up as a log entry
                print 'Warning: Import of module {} failed: {}'.format(module, e)


# Import later to avoid workers failing to start in case of mysql support missing in a worker
# mdb = _import_db_driver()

class MySqlWrapper(object):

    '''Shard-aware SQL adapter
    sql().execute('SELECT 1').result()
    '''

    def __init__(self, shards, user='nagios', password='', timeout=60000, shard=None):
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
        '''

        if not shards:
            raise ValueError('SqlWrapper: No shards defined')
        if shard and not shards.get(shard):
            raise ValueError('SqlWrapper: Shard {} not found in shards definition'.format(shard))

        self._cursors = []
        self._stmt = None

        mdb = _import_db_driver()

        for shard_def in ([shards[shard]] if shard else shards.values()):
            m = CONNECTION_RE.match(shard_def)
            if not m:
                raise ValueError('Invalid shard connection: {}'.format(shard_def))
            try:
                conn = mdb.connect(host=m.group('host'), user=user, passwd=password, db=m.group('dbname'),
                                   port=(int(m.group('port')) if int(m.group('port')) > 0 else DEFAULT_PORT),
                                   connect_timeout=timeout)
            except Exception, e:
                raise DbError(str(e), operation='Connect to {}'.format(shard_def)), None, sys.exc_info()[2]

            # TODO: Find a way to enforce readonly=True as it is done in postgres Wrapper
            # TODO: Do we need to set charset="utf8" and use_unicode=True in connection?

            conn.autocommit(True)
            self._cursors.append(conn.cursor(mdb.cursors.DictCursor))

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
                        for k, v in row.items():
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

    def results(self):
        '''return many rows'''

        results = []
        try:
            for cur in self._cursors:
                try:
                    cur.execute(self._stmt)
                    rows = cur.fetchmany(MAX_RESULTS)
                    for row in rows:
                        results.append(dict(row))
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self._stmt), None, sys.exc_info()[2]
        return results


if __name__ == '__main__':
    default_dbname = 'mysql'
    default_sql_stmt = 'SELECT VERSION()'  # SELECT Host,User FROM user

    if len(sys.argv) in (6, 7):
        if len(sys.argv) == 7:
            shards = {'test': sys.argv[1] + ':' + sys.argv[2] + '/' + sys.argv[3]}
            sql_stmt = sys.argv[6]
        else:
            print 'executing default statement:', default_sql_stmt
            shards = {'test': sys.argv[1] + ':' + sys.argv[2] + '/' + default_dbname}
            sql_stmt = default_sql_stmt

        check = MySqlWrapper(shards, user=sys.argv[4], password=sys.argv[5])
        # print '>>> many results:\n', check.execute(sql_stmt).results()
        print '>>> one result:\n', check.execute(sql_stmt).result()
    else:
        print '{} <host> <port> <dbname> <user> <password> [sql_stmt]'.format(sys.argv[0])
