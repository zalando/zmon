#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Server module for exposing an rpc interface for clients to remotely control a local ProcessManager
"""

import os
import sys
import signal
import settings
import logging

if __name__ == '__main__':
    import logging.config
    logging.config.dictConfig(settings.RPC_SERVER_CONF['LOGGING'])

logger = logging.getLogger(__name__)

from pprint import pformat

from process_controller import ProcessController
import worker
import rpc_utils


def save_pid(abort_pidfile=False):
    pid = os.getpid()
    pid_file = os.path.join(settings.data_dir, 'rpc_server.pid')
    if abort_pidfile and os.path.isfile(pid_file):
        print >>sys.stderr, 'pid file {} already exists. Is another process running? Aborting!'.format(pid_file)
        sys.exit(1)
    with open(pid_file, 'w') as f:
        f.write(str(pid))


def sigterm_handler(signum, frame):
    # this will propagate the SystemExit exception all around, so we can quit listening loops, cleanup and exit
    sys.exit(0)


class ProcessControllerProxy(rpc_utils.RpcProxy):
    """
    A proxy class to expose some methods of multiprocess manager server to listen to remote requests,
    possible request are:
     1. start N more child processes
     2. terminate processes with pid1, pid2, ...
     3. report running statistics
     4. report status of process with pid1
     5. terminate all child processes
     6. terminate yourself
    """

    exposed_obj_class = ProcessController

    valid_methods = ['spawn_many', 'list_running', 'list_stats', 'start_action_loop', 'stop_action_loop',
                     'is_action_loop_running', 'get_dynamic_num_processes', 'set_dynamic_num_processes',
                     'get_action_policy', 'set_action_policy', 'available_action_policies', 'terminate_all_processes',
                     'terminate_process', 'mark_for_termination']

    def list_running(self):
        return pformat(self.get_exposed_obj().list_running())

    def list_stats(self):
        return pformat(self.get_exposed_obj().list_stats())

    def on_exit(self):
        self.get_exposed_obj().terminate_all_processes()  # TODO: Think why exit codes are sometimes -15 and others 0


class MainProcess(object):

    def __init__(self):
        save_pid()
        signal.signal(signal.SIGTERM, sigterm_handler)

    def start_proc_control(self):
        self.proc_control = ProcessController(default_target=worker.start_worker, action_policy='report')

    def start_rpc_server(self):

        rpc_proxy = ProcessControllerProxy(self.proc_control)

        rpc_utils.start_RPC_server(settings.RPC_SERVER_CONF['HOST'],
                                   settings.RPC_SERVER_CONF['PORT'],
                                   settings.RPC_SERVER_CONF['RPC_PATH'],
                                   rpc_proxy)


def main(config=None):

    save_pid(abort_pidfile=True)

    signal.signal(signal.SIGTERM, sigterm_handler)

    proc_control = ProcessController(default_target=worker.start_worker,
                                     action_policy='report', always_add_kwargs={'external_config': config})

    rpc_proxy = ProcessControllerProxy(proc_control)

    rpc_utils.start_RPC_server(settings.RPC_SERVER_CONF['HOST'],
                               settings.RPC_SERVER_CONF['PORT'],
                               settings.RPC_SERVER_CONF['RPC_PATH'],
                               rpc_proxy)


if __name__ == '__main__':

    main()
