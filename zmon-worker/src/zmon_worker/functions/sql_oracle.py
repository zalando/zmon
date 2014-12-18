#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from zmon_worker.errors import DbError

# default port Oracle Net Listener port
DEFAULT_PORT = 1521
MAX_RESULTS = 100


def _check_oracle_env():
    if 'ORACLE_HOME' not in os.environ or 'LD_LIBRARY_PATH' not in os.environ or os.environ['ORACLE_HOME'] \
        not in os.environ['LD_LIBRARY_PATH'] or not os.path.isdir(os.environ['ORACLE_HOME']):
        raise Exception('Environmet variables ORACLE_HOME and LD_LIBRARY_PATH are not correctly set')


def _import_db_driver():
    try:
        _check_oracle_env()
        _cx_Oracle = __import__('cx_Oracle', globals(), locals(), [], -1)
    except Exception:
        # do we want to take some action here?
        raise
    return _cx_Oracle


# Import later to avoid workers failing to start in case of errors on cx_Oracle compilation or missing env vars
# cx_Oracle = _import_db_driver()

class SqlOracleWrapper(object):

    '''Oracle SQL adapter
    sql().execute('SELECT 1').result()
    '''

    def __init__(self, host, port, sid, user='nagios', password='', enabled=True):
        self._stmt = None
        self._dsn_tns = None
        self._enabled = enabled
        self.__cx_Oracle = None
        self.__conn = None
        self.__cursor = None

        if self._enabled:
            self.__cx_Oracle = _import_db_driver()
            port = (int(port) if port and str(port).isdigit() else DEFAULT_PORT)
            try:
                self._dsn_tns = self.__cx_Oracle.makedsn(host, port, sid)
                self.__conn = self.__cx_Oracle.connect(user, password, self._dsn_tns)
                self.__cursor = self.__conn.cursor()
            except Exception, e:
                raise DbError(str(e), operation='Connect to dsn={}'.format(self._dsn_tns)), None, sys.exc_info()[2]

    def execute(self, stmt):
        self._stmt = stmt
        return self

    def result(self, agg=sum):
        '''return single row result, will result primitive value if only one column is selected'''

        result = {}
        try:
            if self._enabled and self.__cx_Oracle:
                cur = self.__cursor
                try:
                    cur.execute(self._stmt)
                    desc = [d[0] for d in cur.description]  # Careful: col names come out all uppercase
                    row = cur.fetchone()
                    if row:
                        result = dict(zip(desc, row))
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self._stmt), None, sys.exc_info()[2]

        if len(result) == 1:
            return result.values()[0]
        else:
            return result

    def results(self):
        '''return many rows'''

        results = []
        try:
            if self._enabled and self.__cx_Oracle:
                cur = self.__cursor
                try:
                    cur.execute(self._stmt)
                    desc = [d[0] for d in cur.description]  # Careful: col names come out all uppercase
                    rows = cur.fetchmany(MAX_RESULTS)
                    for row in rows:
                        row = dict(zip(desc, row))
                        results.append(row)
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self._stmt), None, sys.exc_info()[2]
        return results


if __name__ == '__main__':

    default_sql_stmt = "SELECT 'OK' from dual"

    if len(sys.argv) in (6, 7):
        check = SqlOracleWrapper(sys.argv[1], sys.argv[2], sys.argv[3], user=sys.argv[4], password=sys.argv[5])
        if len(sys.argv) == 7:
            sql_stmt = sys.argv[6]
        else:
            print 'executing default statement:', default_sql_stmt
            sql_stmt = default_sql_stmt

        # print '>>> one result:\n', check.execute(sql_stmt).result()
        print '>>> many results:\n', check.execute(sql_stmt).results()
    else:
        print '{} <host> <port> <sid> [sql_stmt]'.format(sys.argv[0])

