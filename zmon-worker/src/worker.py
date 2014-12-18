# -*- coding: utf-8 -*-
"""
Execution script
"""

import sys
import os
import json
import settings
import logging


def _set_logging(log_conf):
    #substituting {pid} in log handlers
    for handler_name, handler_dict in log_conf['handlers'].items():
        if '{pid}' in handler_dict.get('filename', ''):
            log_conf['handlers'][handler_name]['filename'] = log_conf['handlers'][handler_name]['filename']\
            .format(pid=os.getpid())

    import logging.config
    logging.config.dictConfig(log_conf)



def start_worker(**kwargs):
    """
    A simple wrapper for workflow.start_worker(role) , needed to solve the logger import problem with multiprocessing
    :param role: one of the constants workflow.ROLE_...
    :return:
    """
    _set_logging(settings.LOGGING)

    import workflow

    workflow.start_worker_for_queue(**kwargs)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print >> sys.stderr, "\nWrong command line parameters:\n  " \
                             "usage: {0} <kwargs_json>".format(sys.argv[0])
        sys.exit(1)

    kwargs = json.loads(sys.argv[1])

    print "unmanaged worker started with kwargs: {}".format(kwargs)

    start_worker(**kwargs)
