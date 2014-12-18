#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import logging
import re
import shlex
import subprocess32
from functools import partial, wraps
from zmon_worker.errors import CheckError, NagiosError

# only return 95% of diskspace because of http://unix.stackexchange.com/questions/7950/reserved-space-for-root-on-a-filesystem-why
USABLE_DISKSPACE_FACTOR = 0.95


def error_wrapped(parser):

    @wraps(parser)
    def wrapper(*args, **kwargs):
        try:
            result = parser(*args, **kwargs)
        except Exception:
            raise NagiosError(args[0])
        else:
            return result

    return wrapper


def fix_sub32_exc(e):
    '''Quick and dirty way to deal with subprocess32 bugs. See PF-4190'''

    if isinstance(e, subprocess32.TimeoutExpired):
        for field in ['output', 'timeout', 'cmd']:
            if not hasattr(e, field):
                setattr(e, field, '--')
    if isinstance(e, subprocess32.CalledProcessError):
        for field in ['returncode', 'output', 'cmd']:
            if not hasattr(e, field):
                setattr(e, field, '--')
    return e


class NagiosWrapper(object):

    def __init__(self, host, logger=None, exasol_user='nagios', exasol_password='', lounge_mysql_user='nagios',
                 lounge_mysql_password='', hetcrawler_proxy_user='', hetcrawler_proxy_pass=''):
        self.host = host
        self.logger = logger or logging.getLogger()
        self.__nrpe_config = {  # example to check non-default memcached:
                              # nagios().nrpe('check_memcachestatus', port=11212)
                              # example to check non-default logwatch:
                              # requires NRPE: command[check_all_disks]=/usr/lib/nagios/plugins/check_disk -w "$ARG1$" -c "$ARG2$" -u "$ARG3$"
            'check_diff_reverse': {'args': '-a /proc/meminfo CommitLimit Committed_AS kB 1048576 524288',
                                   'parser': self._to_dict_commitdiff},
            'check_disk': {'args': '-a 15% 7% /', 'parser': self._parse_memory},
            'check_all_disks': {'args': '-a 15% 7% MB', 'parser': self._parse_disks},
            'check_fiege-avis-file': {'args': '', 'parser': self._to_dict_from_text},
            'check_findfiles': {'args': '-a 20,20,20 20,20,20 {directory} {epoch} found',
                                'parser': partial(self._to_dict, func=int),
                                'parameters': {'directory': '', 'epoch': 1}},
            'check_findfiles_names': {'args': '-a 20,20,20 20,20,20 {directory} {epoch} found {name}',
                                      'parser': partial(self._to_dict, func=int),
                                      'parameters': {'directory': '', 'epoch': 1,
                                      'name': ''}},
            'check_findfiles_names_exclude': {'args': '-a 20,20,20 20,20,20 {directory} {epoch} found {name}',
                                      'parser': partial(self._to_dict, func=int),
                                      'parameters': {'directory': '', 'epoch': 1,
                                      'name': ''}},
            'check_hpacucli_py': {'args': '', 'parser': json.loads},
            'check_hpacucli': {'args': '', 'parser': self._to_dict_hpraid},
            'check_hpasm_dl380p_gen8_fix': {'args': '-a 14:60 15:60', 'parser': self._to_dict_hpasm},
            'check_hpasm_fix_power_supply': {'args': '-a 14:60 15:60', 'parser': self._to_dict_hpasm},
            'check_hpasm_gen8': {'args': '-a 14:60 15:60', 'parser': self._to_dict_hpasm},
            'check_inodes': {'args': '', 'parser': json.loads},
            'check_iostat': {'args': '-a 32000,30000 64000,40000 {disk}', 'parser': self._to_dict_iostat,
                             'parameters': {'disk': 'sda'}},
            'check_list_timeout': {
                'args': '-a "ls {path}" {timeout}',
                'parameters': {'path': '/data/production/', 'timeout': 10},
                'parser': self._to_dict,
                'pre_run_hook': self._check_path_chars,
            },
            'check_load': {'args': '-a 15,14,12 20,17,15', 'parser': self._to_dict},
            'check_mailq_postfix': {'args': '-a 10 5000', 'parser': partial(self._to_dict, func=int)},
            'check_postfix_queue.sh': {'parser': partial(self._to_dict, func=int)},
            'check_memcachestatus': {'args': '-a 9000000,550,10000,100,6000,5000,20481024,20481024 99000000,1000,12000,200,8000,7000,40961024,40961024 127.0.0.1 {port}',
                                     'parser': self._to_dict, 'parameters': {'port': 11211}},
            'check_ntp_time': {'args': '-a 1 2 10 {ntp_server}', 'parser': self._to_dict},
            'check_openmanage': {'args': '', 'parser': self._to_dict_hpasm},
            'check_subdomain_redirect': {'args': '', 'parser': self._to_dict_from_text},
            'check_icmp': {'args': '-a {targethost} {num_of_packets} {timeout}', 'parser': self._to_dict,
                           'parameters': {'targethost': 'default', 'num_of_packets': 5, 'timeout': 10}},
            'check_tcp': {'args': '-a {targethost} {port} {timeout}', 'parser': self._to_dict,
                          'parameters': {'targethost': 'default', 'port': 22, 'timeout': 10}},
            'check_tcp_str': {'args': '-a {targethost} {port} {timeout} {expected}', 'parser': self._to_dict,
                              'parameters': {
                'targethost': 'default',
                'port': 22,
                'timeout': 10,
                'expected': 'SSH-2.0-OpenSSH',
            }},
            'check_ssl': {'args': '-a {targethost} {port} {timeout}', 'parser': self._to_dict,
                          'parameters': {'targethost': 'default', 'port': 443, 'timeout': 10}},
            'check_statistics.pl': {'args': '', 'parser': self._to_dict},
            'check_oracle': {'args': '{user_args}', 'parser': self._to_dict, 'parameters': {'user_args': ''}},
            'check_flocked_file': {'args': '-a {lockfile}', 'parser': self._to_dict_from_text},
            'check_apachestatus_uri': {'args': '-a 16000,10000,48 32000,20000,64 {url}', 'parser': self._to_dict,
                                       'parameters': {'url': 'http://127.0.0.1/server-status?auto'}},
            'check_command_procs': {'args': '-a 250 500 {process}', 'parser': self._to_dict_procs,
                                    'parameters': {'process': 'httpd'}},
            'check_http_expect_port_header': {'args': '-a 2 8 60 {ip} {url} {redirect} {size} {expect} {port} {hostname}',
                                              'parser': self._to_dict, 'parameters': {
                'ip': 'localhost',
                'url': '/',
                'redirect': 'warning',
                'size': '9000:90000',
                'expect': '200',
                'port': '88',
                'hostname': 'www.example.com',
            }},
            'check_mysql_processes': {'args': '-a 30 60 {host} {port} {user} {password}',
                                      'parser': self._to_dict_mysql_procs, 'parameters': {
                'host': 'localhost',
                'port': '/var/lib/mysql/mysql.sock',
                'user': lounge_mysql_user,
                'password': lounge_mysql_password,
            }},
            'check_mysqlperformance': {'args': '-a 10000,1500,5000,500,750,100,100,1,5000,30,60,500,10,30 15000,3000,10000,750,1000,250,250,5,7500,60,300,1000,20,60 {host} {port} Questions,Com_select,Qcache_hits,Com_update,Com_insert,Com_delete,Com_replace,Aborted_clients,Com_change_db,Created_tmp_disk_tables,Created_tmp_tables,Qcache_not_cached,Table_locks_waited,Select_scan {user} {password}',
                                       'parser': self._to_dict, 'parameters': {
                'host': 'localhost',
                'port': '/var/lib/mysql/mysql.sock',
                'user': lounge_mysql_user,
                'password': lounge_mysql_password,
            }},
            'check_mysql_slave': {'args': '-a 3 60 {host} {port} {database} {user} {password}',
                                  'parser': self._to_dict_mysql_slave, 'parameters': {
                'host': 'localhost',
                'port': '/var/lib/mysql/mysql.sock',
                'database': 'zlr_live_global',
                'user': lounge_mysql_user,
                'password': lounge_mysql_password,
            }},
            'check_stunnel_target': {
                        'args': '-a {target} {user} {password}',
                        'parser': self._to_dict,
                        'parameters': {
                            'target': 'www.example.com',
                            'user': hetcrawler_proxy_user,
                            'password': hetcrawler_proxy_pass,
                        },
            },
            'check_lounge_queries': {'args': '', 'parser': self._to_dict_lounge_queries},
            'check_newsletter': {'args': '-p {port}', 'parser': self._to_dict_newsletter,
                                 'parameters': {'port': '5666'}},
            'check_nfs_mounts': {'args': '', 'parser': self._to_dict_list},
            'check_kdc': {'args': '', 'parser': json.loads},
            'check_kadmin': {'args': '', 'parser': json.loads},
            'check_ssl_cert': {'args': '-a 60 30 {host_ip} {domain_name}', 'parser': partial(self._to_dict, func=int),
                               'parameters': {'host_ip': '127.0.0.1', 'domain_name': 'www.example.com'}},
        }

        self.__local_config = {
            'check_subdomain_redirect.py': {'args': '', 'parser': self._to_dict_from_text},
            'check_ping': {'args': '-H {} -w 5000,100% -c 5000,100% -p 1'.format(self.host), 'parser': self._to_dict},
            'check_snmp_mem_used-cached.pl': {'args': '-H {} -w 100,100,100 -c 100,100,100 -C public -f'.format(self.host),
                                              'parser': self._to_dict},
            'check_icmp': {'args': '-H {} -n {{num_of_packets}} -t {{timeout}}'.format(self.host),
                           'parser': self._to_dict, 'parameters': {'num_of_packets': 5, 'timeout': 10}},
            'check_tcp': {'args': '-H {} -p {{port}} -t {{timeout}}'.format(self.host), 'parser': self._to_dict,
                          'parameters': {'port': 22, 'timeout': 10}},
            'check_tcp_str': {'args': '-H {} -p {{port}} -t {{timeout}} -e {{expected}}'.format(self.host),
                              'parser': self._to_dict, 'parameters': {'port': 22, 'timeout': 10,
                              'expected': 'SSH-2.0-OpenSSH'}},
            'check_ssl': {'args': '-H {} -p {{port}} -t {{timeout}} -S'.format(self.host), 'parser': self._to_dict,
                          'parameters': {'port': 443, 'timeout': 10}},
            'check_dns': {'args': '-H {host} -s {dns_server} -t {timeout}', 'parser': self._to_dict,
                          'parameters': {'timeout': 5}},
            'check_snmp_process.pl': {'args': '-H {} -C {{community}} -F -n {{name}} -c {{critical}} -w {{warn}} -o {{octets}} {{extra}}'.format(self.host),
                                      'parser': self._to_dict, 'parameters': {
                'timeout': 5,
                'octets': 2400,
                'warn': 1,
                'critical': 1,
                'community': 'public',
                'extra': '-r -2',
            }},
            # check_xmlrpc.rb:  BI checks for PF-3558
            # possible user_args:
            # Exasol: backup state -> '-check-backup'  (default)
            # Exasol: DB-Status -> '--rpc getDatabaseState --ok'
            # Exasol: Node status -> '--check-node-states -w 0 -c 1'
            # Exasol: Verbindungs-Status -> '--rpc getDatabaseConnectionState --ok yes'
            'check_xmlrpc.rb': {'args': '--url http://{user}:{password}@{targethost}/cluster1/db_exa_db1 {user_args}',
                                'parser': self._to_dict_newsletter, 'parameters': {
                'targethost': '10.229.12.212',
                'user': exasol_user,
                'password': exasol_password,
                'user_args': '-check-backup',
            }},
            'check_ssl_cert': {'args': '-w 60 -c 30 -H {host_ip} -n {domain_name} -r /etc/ssl/certs --altnames', 'parser': partial(self._to_dict, func=int),
                               'parameters': {'host_ip': '127.0.0.1', 'domain_name': 'www.example.com'}},
            'check-ldap-sync.pl': {'args': '', 'parser': json.loads},
        }

        self.__win_config = {
            'CheckCounter': {'args': '-a "Counter:ProcUsedMem=\\Process({process})\\Working Set" ShowAll MaxWarn=1073741824 MaxCrit=1073741824',
                             'parser': partial(self._to_dict_win, func=int), 'parameters': {'process': 'eo_server'}},
            'CheckCPU': {'args': '-a warn=100 crit=100 time=1 warn=100 crit=100 time=5 warn=100 crit=100 time=10',
                         'parser': partial(self._to_dict_win, func=int)},
            'CheckDriveSize': {'args': '-a CheckAll ShowAll perf-unit=M', 'parser': self._to_dict_win},
            'CheckEventLog': {'args': '-a file="{log}" MaxWarn=1 MaxCrit=1 "filter={query}" truncate=800 unique "syntax=%source% (%count%)"',
                              'parser': partial(self._to_dict_win, func=int), 'parameters': {'log': 'application',
                              'query': 'generated gt -7d AND type=\'error\''}},
            'CheckFiles': {'args': '-a "path={path}" "pattern={pattern}" "filter={query}" MaxCrit=1',
                           'parser': partial(self._to_dict_win, func=int),
                           'parameters': {'path': 'C:\\Import\\Exchange2Clearing', 'pattern': '*.*',
                           'query': 'creation lt -1h'}},
            'CheckLogFile': {'args': '-a file="{logfile}" column-split="{seperator}" "filter={query}"',
                             'parser': self._to_dict_win_log,
                             'parameters': {'logfile': 'c:\Temp\log\maxflow_portal.log', 'seperator': ' ',
                             'query': 'column4 = \'ERROR\' OR column4 = \'FATAL\''}},
            'CheckMEM': {'args': '-a MaxWarn=15G MaxCrit=15G ShowAll perf-unit=M type=physical type=page type=virtual',
                         'parser': self._to_dict_win},
            'CheckProcState': {'args': '-a ShowAll {process}', 'parser': self._to_dict_win_text,
                               'parameters': {'process': 'check_mk_agent.exe'}},
            'CheckServiceState': {'args': '-a ShowAll {service}', 'parser': self._to_dict_win_text,
                                  'parameters': {'service': 'ENAIO_server'}},
            'CheckUpTime': {'args': '-a MinWarn=1000d MinCrit=1000d', 'parser': partial(self._to_dict_win, func=int)},
        }

    def nrpe(self, check, timeout=60, **kwargs):
        config = self.__nrpe_config[check]
        parameters = {}
        parameters.update(config.get('parameters', {}))
        parameters.update(kwargs)
        pre_run_hook_ok = config.get('pre_run_hook', self._check_ok)
        if not pre_run_hook_ok(config.get('parameters', {})):
            raise CheckError('Pre run hook does not accept your parameters')
        cmd_args = config['args'].format(**parameters)
        cmd = shlex.split('/usr/lib/nagios/plugins/check_nrpe -u -H {h} -t {t} -c {c} {a}'.format(h=self.host,
                          t=timeout, c=check, a=cmd_args))
        try:
            output = subprocess32.check_output(cmd, shell=False, timeout=timeout)
        except subprocess32.CalledProcessError, e:
            e = fix_sub32_exc(e)
            if e.returncode < 3:
                output = str(e.output)
            else:
                output = str(e.output)
                return output
        except subprocess32.TimeoutExpired, e:
            e = fix_sub32_exc(e)
            raise NagiosError(str(e)), None, sys.exc_info()[2]
        self.logger.debug('output for cmd (%s): %s', cmd, output)
        return self.__nrpe_config[check]['parser'](output)

    def local(self, check, timeout=60, **kwargs):
        config = self.__local_config[check]
        parameters = {}
        parameters.update(config.get('parameters', {}))
        parameters.update(kwargs)
        pre_run_hook_ok = config.get('pre_run_hook', self._check_ok)
        if not pre_run_hook_ok(config.get('parameters', {})):
            raise CheckError('Pre run hook does not accept your parameters')
        cmd_args = config['args'].format(**parameters)
        cmd = shlex.split('/usr/lib/nagios/plugins/{c} {a}'.format(c=check, a=cmd_args))
        try:
            output = subprocess32.check_output(cmd, shell=False, timeout=timeout)
        except subprocess32.CalledProcessError, e:
            e = fix_sub32_exc(e)
            if e.returncode < 3:
                output = str(e.output)
            else:
                output = str(e.output)
                return output
        except subprocess32.TimeoutExpired, e:
            e = fix_sub32_exc(e)
            raise NagiosError(str(e)), None, sys.exc_info()[2]
        self.logger.debug('output for cmd (%s): %s', cmd, output)
        return self.__local_config[check]['parser'](output)

    def win(self, check, timeout=60, **kwargs):
        config = self.__win_config[check]
        parameters = {}
        parameters.update(config.get('parameters', {}))
        parameters.update(kwargs)
        pre_run_hook_ok = config.get('pre_run_hook', self._check_ok)
        if not pre_run_hook_ok(config.get('parameters', {})):
            raise CheckError('Pre run hook does not accept your parameters')
        cmd_args = config['args'].format(**parameters)
        cmd = shlex.split('/usr/lib/nagios/plugins/check_nrpe -u -H {h} -t {t} -c {c} {a}'.format(h=self.host,
                          t=timeout, c=check, a=cmd_args))
        try:
            output = subprocess32.check_output(cmd, shell=False, timeout=timeout)
        except subprocess32.CalledProcessError, e:
            e = fix_sub32_exc(e)
            if e.returncode < 3:
                output = str(e.output)
            else:
                output = str(e.output)
                return output
        except subprocess32.TimeoutExpired, e:
            e = fix_sub32_exc(e)
            raise NagiosError(str(e)), None, sys.exc_info()[2]
        self.logger.debug('output for cmd (%s): %s', cmd, output)
        return self.__win_config[check]['parser'](output)

    @staticmethod
    def _check_ok(config):
        '''Returns always True (ok) as result.'''

        return True

    @staticmethod
    def _check_path_chars(config):
        return re.match("^[a-zA-Z0-9\/_\-]+$", config['path'])

    @staticmethod
    @error_wrapped
    def _to_dict(output, func=float):
        return dict((a.split('=')[0], func(re.sub('[^0-9.]', '', a.split('=')[1].split(';')[0]))) for a in
                    output.split('|')[-1].split())

    @staticmethod
    @error_wrapped
    def _to_dict_list(output):
        return dict((a, 1) for a in output.split('|')[-1].split())

    @staticmethod
    @error_wrapped
    def _to_dict_olderfiles(output):
        '''try to parse this output:
        OK - 0 files older as 600 min -- 0 files older as 540 min -- total 762 files -- older:

        >>> import json; json.dumps(NagiosWrapper._to_dict_olderfiles('OK - 0 files older as 600 min -- 112 files older as 60 min -- total 831 files -- older:'), sort_keys=True)
        '{"files older than time01": 112, "files older than time02": 0, "total files": 831}'
        '''

        return {'files older than time01': int(output.split(' -- ')[1].split()[0]), 'files older than time02': int(output.split(' -- ')[0].split()[2]), 'total files': int(output.split(' -- ')[2].split()[1])}

    @staticmethod
    @error_wrapped
    def _to_dict_win(output, func=float):
        '''try to parse this output:
        OK: physical memory: 4.8G, page file: 5.92G, virtual memory: 254M|'physical memory %'=29%;6;6 'physical memory'=5028644K;15728640;15728640;0;16776760 'page file %'=18%;53;53 'page file'=6206652K;15728640;15728640;0;33472700 'virtual memory %'=0%;99;99 'virtual memory'=259704K;15728640;15728640;0;8589934464
        '''

        return dict((a.split('=')[0], func(re.sub('[^0-9.]', '', a.split('=')[1].split(';')[0]))) for a in
                    shlex.split(output.split('|')[-1]))

    @staticmethod
    @error_wrapped
    def _to_dict_win_text(output):
        '''try to parse this output:
        OK: ENAIO_server: started
        '''

        po = {'status': output.split(':')[0], 'message': ' '.join(output.split(' ')[1:]).strip(' \n').split('|')[0]}
        if not po['status'] or not po['message']:
            raise NagiosError('Unable to parse {}'.format(output))
        return po

    @staticmethod
    @error_wrapped
    def _to_dict_win_log(output):
        '''try to parse this output:
        c:\Temp\log\maxflow_portal.log2014.04.29: 1 (2014-04-29 15:44:00,741 [5] WARN  BeckIT.MPO.... )
        '''

        if 'Nothing matched' in output:
            return {'count': 0}
        else:
            return {'count': int(output.split(' ')[1].strip(' '))}

    @staticmethod
    @error_wrapped
    def _to_dict_commitdiff(output):
        '''
        try to parse this output:
        CheckDiff OK - CommitLimit-Committed_AS: 24801200 | 24801200;1048576;524288
        '''

        return {(output.split(' ')[-4])[:-1]: int(output.split(' ')[-3])}

    @staticmethod
    @error_wrapped
    def _to_dict_logwatch(output):
        '''
        try to parse this output:
        WARNING - 0 new of 109 Lines on /access.log|newlines=0;100;5000;0;
        or
        OK - 0 new of 109 Lines on /access.log|newlines=0;1000;5000;0;
        '''

        return {'last': int(output.split(' ')[2]), 'total': int(output.split(' ')[5])}

    @staticmethod
    @error_wrapped
    def _to_dict_from_text(output):
        '''
        try to parse this output:
        Status ERROR : Avis-File for Fiege is missing
        or
        Status OK : file is ...
        '''

        return {'status': output.split(' ')[1].strip('\n'), 'message': ' '.join(output.split(' ')[3:]).strip('\n')}

    @staticmethod
    @error_wrapped
    def _to_dict_procs(output):
        '''
        try to parse this output:
        PROCS OK: 33 processes with command name 'httpd'
        '''

        return {'procs': int(output.split(' ')[2])}

    @staticmethod
    @error_wrapped
    def _to_dict_mysql_procs(output):
        '''
        try to parse this output:
        1 threads running. 0 seconds avg
        '''

        return {'threads': int(output.split(' ')[0]), 'avg': int(output.split(' ')[3])}

    @staticmethod
    @error_wrapped
    def _to_dict_mysql_slave(output):
        '''try to parse this output:
        Uptime: 38127526  Threads: 2  Questions: 42076974272  Slow queries: 1081545  Opens: 913119  Flush tables: 889  Open tables: 438  Queries per second avg: 1103.585 Slave IO: Yes Slave SQL: Yes Seconds Behind Master: 0
        '''

        po = dict(re.findall('([a-z][a-z0-9 ]+): ([a-z0-9.()]+)', output, re.IGNORECASE))
        for k, v in po.items():
            if not re.match('[a-z()]', v, re.IGNORECASE):
                po[k] = float(v)
        return po

    @staticmethod
    @error_wrapped
    def _to_dict_lounge_queries(output):
        '''try to parse this output:
        QUERY OK: 'SELECT COUNT(*) FROM global_orders WHERE ( billing_address LIKE '%Rollesbroich%' OR shipping_address LIKE '%Rollesbroich%' OR email LIKE '%Rollesbroich%' OR billing_address LIKE '%Süddeutsche TV%' OR shipping_address LIKE '%Süddeutsche TV%' OR email='sparfuchs-galileo@gmx.de' ) AND order_date >= DATE_SUB(CURDATE(),INTERVAL 1 DAY);' returned 0.000000
        '''

        return {'status': ' '.join(output.split()[:2]).strip(':'), 'query': ' '.join(output.split()[2:-2]),
                'result': float(output.split()[-1])}

    @staticmethod
    @error_wrapped
    def _to_dict_iostat(output):
        '''
        try to parse this output:
        OK - IOread 0.00 kB/s, IOwrite 214.80 kB/s  on sda with  31.10 tps |ioread=0.00;32000;64000;0;iowrite=214.80;30000;40000;0;
        '''

        return {'ioread': float(output.split(' ')[3]), 'iowrite': float(output.split(' ')[6]),
                'tps': float(output.split(' ')[13])}

    @staticmethod
    @error_wrapped
    def _to_dict_hpraid(output):
        '''
        try to parse this output:
        logicaldrive 1 (68.3 GB, RAID 1, OK) -- physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SAS, 146 GB, OK) -- physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SAS, 72 GB, OK) -- logicaldrive 2 (279.4 GB, RAID 1, OK) -- physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SAS, 300 GB, OK) -- physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SAS, 300 GB, OK) -- logicaldrive 3 (279.4 GB, RAID 1, OK) -- physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SAS, 300 GB, OK) -- physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SAS, 300 GB, OK) --
        '''

        return dict((b.split(' ')[0] + '_' + b.split(' ')[1], b.split(',')[-1].strip(' )')) for b in [a.strip(' --\n')
                    for a in output.split(' -- ')])

    @staticmethod
    @error_wrapped
    def _to_dict_newsletter(output):
        '''
        try to parse this output:
        OK: Not in timeframe (02:25:00 - 09:00:00)
        or
        CRITICAL: NL not processed for appdomain 17, Not processed for appdomain 18
        '''

        return {'status': output.split(': ')[0], 'messages': output.split(': ')[-1].strip('\n').split(',')}

    @staticmethod
    @error_wrapped
    def _to_dict_hpasm(output):
        '''
        try to parse this output:
        OK - System: 'proliant dl360 g6', S/N: 'CZJ947016M', ROM: 'P64 05/05/2011', hardware working fine, da: 3 logical drives, 6 physical drives cpu_0=ok cpu_1=ok ps_2=ok fan_1=46% fan_2=46% fan_3=46% fan_4=46% temp_1=21 temp_2=40 temp_3=40 temp_4=35 temp_5=34 temp_6=37 temp_7=32 temp_8=36 temp_9=32 temp_10=36 temp_11=32 temp_12=33 temp_13=48 temp_14=29 temp_15=32 temp_16=30 temp_17=29 temp_18=39 temp_19=37 temp_20=38 temp_21=45 temp_22=42 temp_23=39 temp_24=48 temp_25=35 temp_26=46 temp_27=35 temp_28=71 | fan_1=46%;0;0 fan_2=46%;0;0 fan_3=46%;0;0 fan_4=46%;0;0 'temp_1_ambient'=21;42;42 'temp_2_cpu#1'=40;82;82 'temp_3_cpu#2'=40;82;82 'temp_4_memory_bd'=35;87;87 'temp_5_memory_bd'=34;78;78 'temp_6_memory_bd'=37;87;87 'temp_7_memory_bd'=32;78;78 'temp_8_memory_bd'=36;87;87 'temp_9_memory_bd'=32;78;78 'temp_10_memory_bd'=36;87;87 'temp_11_memory_bd'=32;78;78 'temp_12_power_supply_bay'=33;59;59 'temp_13_power_supply_bay'=48;73;73 'temp_14_memory_bd'=29;60;60 'temp_15_processor_zone'=32;60;60 'temp_16_processor_zone'=3
        or
        OK - ignoring 16 dimms with status 'n/a' , System: 'proliant dl360p gen8', S/N: 'CZJ2340R6C', ROM: 'P71 08/20/2012', hardware working fine, da: 1 logical drives, 4 physical drives
        '''

        return {'status': output.split(' - ')[0], 'message': output.split(' - ')[-1].strip('\n')}

    @staticmethod
    @error_wrapped
    def _parse_memory(output):
        result = dict((a.split('=')[0], a.split('=')[1].split(';')[0]) for a in output.split('|')[-1].split())
        conv = {
            't': 1000000000,
            'tb': 1000000000,
            'tib': 1073741824,
            'g': 1000000,
            'gb': 1000000,
            'gib': 1048576,
            'm': 1000,
            'mb': 1000,
            'mib': 1024,
            'k': 1,
            'kb': 1,
            'kib': 1.024,
        }
        p = re.compile(r'^(\d+(?:\.\d+)?)(?:\s+)?(\w+)?$', re.I)

        for k in result:
            parts = p.findall(result[k])
            if len(parts):
                v, u = parts[0]
                result[k] = (float(v) * conv[u.lower()] if u and u.lower() in conv else float(v))

        return result

    @staticmethod
    @error_wrapped
    def _parse_disks(output):
        '''try to parse output of /usr/lib/nagios/plugins/check_disk -w 10% -c 5%  -u MB

        >>> import json; json.dumps(NagiosWrapper._parse_disks('DISK OK - free space: / 80879 MB (69% inode=99%); /dev 64452 MB (99% inode=99%); /selinux 0 MB (100% inode=99%); | /=35303MB;110160;116280;0;122401 /dev=0MB;58006;61229;0;64452 /selinux=0MB;0;0;0;0'), sort_keys=True)
        '{"/": {"total_mb": 116280, "used_mb": 35303}, "/dev": {"total_mb": 61229, "used_mb": 0}}'
        '''

        r = re.compile('[^0-9.]')
        performance_data = output.split('|')[-1]
        result = dict((m[0], {'used_mb': int(r.sub('', f[0])), 'total_mb': int(int(f[4]) * USABLE_DISKSPACE_FACTOR)})
                      for (m, f) in [[s.split(';') for s in a.split('=')] for a in performance_data.split()]
                      if int(f[4]) != 0)
        return result


if __name__ == '__main__':
    if len(sys.argv) == 3:
        checkname = sys.argv[2]
        check = NagiosWrapper(sys.argv[1])
        print json.dumps(check.nrpe(checkname), indent=4)
    elif len(sys.argv) == 4:
        checkname = sys.argv[2]
        query = sys.argv[3]
        check = NagiosWrapper(sys.argv[1])
        print json.dumps(check.win(checkname, query=query), indent=4)
    elif len(sys.argv) == 5:
        checkname = sys.argv[2]
        path = sys.argv[3]
        query = sys.argv[4]
        check = NagiosWrapper(sys.argv[1])
        print json.dumps(check.win(checkname, path=path, query=query), indent=4)
    elif len(sys.argv) == 6:
        checkname = sys.argv[2]
        directory = sys.argv[3]
        epoch = sys.argv[4]
        name = sys.argv[5]
        check = NagiosWrapper(sys.argv[1])
        print json.dumps(check.nrpe(checkname, directory=directory, epoch=epoch, name=name), indent=4)
