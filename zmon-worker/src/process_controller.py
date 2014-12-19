# -*- coding: utf-8 -*-
"""
Logic for controlling worker processes
"""

import os
import signal
import time
import copy
import logging

from multiprocessing import Process
from threading import Thread

logger = logging.getLogger(__name__)


class ProcessController(object):
    """
    Class to handle a bunch of child processes
    what can it do:
    0. define a common target function for every process?
    1. spawn N processes that execute the target function, store references to objects and its pid
    2. spawn more process after some are running
    3. terminate some process *(by pid?)
    4. spawn a thread loop for checking the health of child processes *(and take some action if some process dies)?
    5. dynamically change the policy on how to react to process dies *(use queue for incoming requests?)
    """

    action_policies = ('report', 'dynamic_num', 'dynamic_throughput')

    proc_stat_element = {'begin_time': -1, 'end_time': -1, 'alive': False, 'rebel': False, 'pid': 0, 'exitcode': 0,
                         'mem': -1, 'abnormal_termination': False}

    def __init__(self, default_target=None, default_args=None, default_kwargs=None, always_add_kwargs=None,
                 action_policy='report', min_processes=2, max_processes=1000, start_action_loop=True):

        self.default_target = default_target
        self.default_args = default_args if isinstance(default_args, (tuple, list)) else ()
        self.default_kwargs = default_kwargs if isinstance(default_kwargs, dict) else {}
        self.always_add_kwargs = always_add_kwargs if isinstance(always_add_kwargs, dict) else {}

        self.proc_dict = {}    # { proc_name : proc}

        self.proc_rebel = {}   # { proc_name : proc} -> for processes that refuse to die
        self.proc_stats = {}   # { proc_name : {'begin_time':T0, 'end_time': T1, 'alive' : bool1, ... } }

        self.proc_args = {}    # { proc_name : {'target':None, 'args':[...], 'kwargs'={...} }}

        self.pid_to_pname = {}   # {pid: proc_name}

        self.pids_for_termination = []  # [ pid1, pid2, ....]

        self.limbo_proc_dict = {}       # {proc_name : proc}

        self.max_killed_stats = 5000         # max number of dead proc stats to keep around in memory
        self.min_processes = min_processes
        self.max_processes = max_processes
        self.count_stop_condition = 0        # counter of consecutive stop conditions found
        self.consecutive_stop_condition = 5        # counter of consecutive stop conditions found
        self.gracetime_stop_condition = 60   # number of seconds to wait before a final stop condition check

        self._thread_action_loop = None
        self.stop_action = True
        self.action_loop_interval = 2      # seconds between each actions pass
        self.set_action_policy(action_policy)
        self.set_dynamic_num_processes(5)  # number of process to maintain alive when action_policy == 'dynamic_num'

        self._tstamp_clean_old_proc_stats = -1    # timestamp of the last execution of _clean_old_proc_stats()
        self._tdelta_clean_old_proc_stats = 300   # frequency of __clean_old_proc_stats()

        if start_action_loop:
            self.start_action_loop()

    def spawn_process(self, target=None, args=None, kwargs=None):

        args = args if isinstance(args, (tuple, list)) else ()
        kwargs = kwargs if isinstance(kwargs, dict) else {}

        if self.max_processes == len(self.proc_dict):
            raise Exception("maximum number of processes reached!!!")

        target = target or self.default_target
        args = args or self.default_args
        kwargs = dict(kwargs if kwargs else self.default_kwargs)
        kwargs.update(self.always_add_kwargs)

        try:
            proc = Process(target=target, args=args, kwargs=kwargs)
            proc.start()
            pname = proc.name

            # creating entry in running process table
            self.proc_dict[pname] = proc

            # mapping pid -> pname
            self.pid_to_pname[proc.pid] = pname

            # store process arguments to relaunch it if it dies
            self.proc_args[pname] = dict(target=target, args=args, kwargs=kwargs)

            # creating entry in stats table
            self.proc_stats[pname] = dict(self.proc_stat_element)
            self.proc_stats[pname]['pid'] = proc.pid
            self.proc_stats[pname]['alive'] = proc.is_alive()
            self.proc_stats[pname]['begin_time'] = time.time()    # use self._format_time() to get datetime format

        except Exception:
            logger.exception("Spawn of process failed. Caught exception with details: ")
            raise

        return pname

    def spawn_many(self, N, target=None, args=None, kwargs=None):

        logger.info('>>>>>>> spawn_many: %d, %s, %s', N, args, kwargs)

        args = args if isinstance(args, (tuple, list)) else ()
        kwargs = kwargs if isinstance(kwargs, dict) else {}

        n_success = 0
        for i in range(N):
            try:
                self.spawn_process(target=target, args=args, kwargs=kwargs)
            except Exception:
                logger.exception('Failed to start process. Reason: ')
            else:
                n_success += 1
        return n_success == N

    def terminate_process(self, proc_name, kill_wait=0.5):

        proc = self.proc_dict.get(proc_name)
        if not proc:
            logger.warn('process: %s not found!!!!!!!!!!!!!!!!!', proc_name)
            return False

        if proc.is_alive():
            logger.warn('terminating process: %s', proc_name)
            proc.terminate()

            time.sleep(kill_wait)

            if proc.is_alive():
                logger.warn('Sending SIGKILL to process with pid=%s', proc.pid)
                os.kill(proc.pid, signal.SIGKILL)

            abnormal_termination = False
        else:
            logger.warn('process: %s is not alive!!!!!!!!!!!!!!!!!', proc_name)
            abnormal_termination = True

        # move proc to limbo and record end time in stats
        self.proc_dict.pop(proc_name, None)
        self.limbo_proc_dict[proc_name] = proc
        self._close_proc_stats(proc, abnormal_termination)
        return True

    def terminate_all_processes(self):

        self.stop_action_loop()   # very important: stop action loop before starting to terminate child processes

        all_pnames = list(self.proc_dict.keys())

        for proc_name in all_pnames:
            self.terminate_process(proc_name,  kill_wait=0.1)

        logger.info("proc_stats after terminate_all_processes() : %s", self.list_stats())
        return True

    def _close_proc_stats(self, proc, abnormal_termination=False):
        # Update proc_stats  {'proc_name' : {'begin_time':T0, 'end_time': T1, 'alive' : bool1,... } }
        pn = proc.name
        if proc.is_alive():
            self.proc_stats[pn]['alive'] = True
            self.proc_stats[pn]['rebel'] = True
        else:
            self.proc_stats[pn]['abnormal_termination'] = abnormal_termination
            self.proc_stats[pn]['end_time'] = time.time()
            self.proc_stats[pn]['alive'] = False
            self.proc_stats[pn]['exitcode'] = proc.exitcode

    def get_info(self, proc_name):
        """
        Get all the info I can of this process, for example:
        1. How long has it been running? *(Do I need an extra pid table for statistics?)
        2. How much memory does it use?
        """
        raise NotImplementedError('Method get_info not implemented yet')

    def list_running(self):
        return [(proc_name, proc.pid) for proc_name, proc in self.proc_dict.items()]

    def list_stats(self):
        proc_stats = copy.deepcopy(self.proc_stats)
        for proc_name, stats in proc_stats.items():
            stats['begin_time'] = self._format_time(stats['begin_time'])
            stats['end_time'] = self._format_time(stats['end_time'])
        return proc_stats

    def _format_time(self, seconds):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds)) if seconds else '--'

    def get_action_policy(self):
        return self.action_policy

    def set_action_policy(self, action_policy):
        if action_policy not in self.action_policies:
            raise Exception('Invalid action policy, possible values are: %s' % ', '.join(self.action_policies))
        self.action_policy = action_policy

    def available_action_policies(self):
        return self.action_policies

    def is_action_loop_running(self):
        return not self.stop_action

    def get_dynamic_num_processes(self):
        return self.dynamic_num_processes

    def set_dynamic_num_processes(self, dynamic_num_processes):
        try:
            assert type(dynamic_num_processes) is int and \
                   self.min_processes <= dynamic_num_processes <= self.max_processes
        except AssertionError:
            raise Exception('dynamic_num_processes passed is not in correct range')
        self.dynamic_num_processes = dynamic_num_processes

    def _clean_old_proc_stats(self):
        """ Remove old stats from dead processes to avoid high memory usage """
        if time.time() - self._tstamp_clean_old_proc_stats > self._tdelta_clean_old_proc_stats:
            self._tstamp_clean_old_proc_stats = time.time()
            et_pn = sorted([(stats['end_time'], pn) for pn, stats in self.proc_stats.copy().items() if stats['end_time'] > 0])
            del_et_pn = et_pn[:len(et_pn)-self.max_killed_stats] if len(et_pn) > self.max_killed_stats else []
            for end_time, pn in del_et_pn:
                stats = self.proc_stats.pop(pn, None)
                logger.warn('Deleting stats of killed process %s to preserve memory: %s', pn, stats)

    def _clean_limbo_procs(self):

        limbo_dict = dict(self.limbo_proc_dict)

        for pname, proc in limbo_dict.items():
            if proc.is_alive():
                logger.error('Fatal: process in limbo in undead state!!!!!')
            else:
                self.pid_to_pname.pop(proc.pid, None)
                self.proc_args.pop(pname, None)
                self.limbo_proc_dict.pop(pname, None)

    def mark_for_termination(self, pid):
        """Given pid will be stored in local variable that marks them for termination in the next action pass"""
        self.pids_for_termination.append(pid)

    def _respawn(self, proc_name):
        # terminate process and spawn another process with same arguments
        pargs = self.proc_args.get(proc_name, {})
        proc = self.proc_dict.get(proc_name)
        pid = proc.pid if proc else '???'
        was_alive = proc.is_alive() if proc else '???'
        self.terminate_process(proc_name, kill_wait=1.0)
        proc_name2 = self.spawn_process(**pargs)
        proc2 = self.proc_dict.get(proc_name2)
        pid2 = proc2.pid if proc2 else '???'
        logger.warn('Respawned process: proc_name=%s, pid=%s, was_alive=%s --> proc_name=%s, pid=%s, args=%s', proc_name, pid, was_alive, proc_name2, pid2, pargs)

    def _action_loop(self):
        """
        A threaded loop that runs every interval seconds to perform autonomous actions
        """
        while not self.stop_action:
            try:
                # action 1: respond to kill requests: terminate marked pid and spawn them again
                term_pids = self.pids_for_termination[:]
                del self.pids_for_termination[:len(term_pids)]

                for pid in term_pids:
                    pname = self.pid_to_pname.get(pid)
                    if pname is not None:
                        if not self.stop_action:
                            self._respawn(pname)
                    else:
                        logger.warn('action_loop found non valid pid: %s', pid)

                # action 2: inspect all processes and react to those that died unexpectedly
                for pname, proc in self.proc_dict.items():
                    if not proc.is_alive() and not self.stop_action:
                        logger.warn('Detected abnormal termination of process pid=%s... attempting restart', proc.pid)
                        self._respawn(pname)

                self._clean_limbo_procs()
                self._clean_old_proc_stats()
            except Exception:
                logger.exception('Error in ProcessController action_loop: ')

            if not self.stop_action:
                time.sleep(self.action_loop_interval)

    def start_action_loop(self, interval=1):
        self.stop_action = False
        self.action_loop_interval = interval

        self._thread_action_loop = Thread(target=self._action_loop)
        self._thread_action_loop.daemon = True
        self._thread_action_loop.start()

    def stop_action_loop(self):
        self.stop_action = True
