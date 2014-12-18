#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from zmon_worker.errors import DbError

logger = logging.getLogger(__name__)

# requires:
# sudo apt-get install freetds-dev
# sudo pip install pymssql

# default port
DEFAULT_PORT = 1433
MAX_RESULTS = 100


def _import_db_driver():
    try:
        _cx_MsSql = __import__('pymssql', globals(), locals(), [], -1)
    except Exception, e:
        logger.exception('Import of module pymssql failed')
        raise
    return _cx_MsSql


class MsSqlWrapper(object):

    # Note: Timeout must be in seconds
    def __init__(self, host, port, database, user='robot_zmon', password='', enabled=True, timeout=60):
        self.__stmt = None
        self.__enabled = enabled

        if self.__enabled:
            self.__cx_MsSql = _import_db_driver()
            port = (int(port) if port and str(port).isdigit() else DEFAULT_PORT)
            try:
                self.__conn = self.__cx_MsSql.connect('{}:{}'.format(host, port), user, password, database, timeout,
                                                      as_dict=True)
                self.__cursor = self.__conn.cursor()
            except Exception, e:
                raise DbError(str(e), operation='Connect to {}:{}'.format(host, port)), None, sys.exc_info()[2]

    def execute(self, stmt):
        self.__stmt = stmt
        return self

    def result(self):
        # return single row result, will result primitive value if only one column is selected

        result = {}
        try:
            if self.__enabled and self.__cx_MsSql:
                cur = self.__cursor
                try:
                    cur.execute(self.__stmt)
                    row = cur.fetchone()
                    if row:
                        result = row
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self.__stmt), None, sys.exc_info()[2]

        if len(result) == 1:
            return result.values()[0]
        else:
            return result

    def results(self):
        # return many rows

        results = []
        try:
            if self.__enabled and self.__cx_MsSql:
                cur = self.__cursor
                try:
                    cur.execute(self.__stmt)
                    rows = cur.fetchmany(MAX_RESULTS)
                    for row in rows:
                        results.append(row)
                finally:
                    cur.close()
        except Exception, e:
            raise DbError(str(e), operation=self.__stmt), None, sys.exc_info()[2]
        return results


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    default_sql_stmt = "SELECT 'ONE ROW' AS COLUMN_NAME"

    if len(sys.argv) in (6, 7):
        check = MsSqlWrapper(sys.argv[1], sys.argv[2], sys.argv[3], user=sys.argv[4], password=sys.argv[5])
        if len(sys.argv) == 7:
            sql_stmt = sys.argv[6]
        else:
            print 'executing default statement:', default_sql_stmt
            sql_stmt = default_sql_stmt

        print '>>> one result:\n', check.execute(sql_stmt).result()
        # print '>>> many results:\n', check.execute(sql_stmt).results()
    else:
        print '{} <host> <port> <database> [sql_stmt]'.format(sys.argv[0])