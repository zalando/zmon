#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import patch
from zmon_worker.functions import NagiosWrapper
from zmon_worker.functions.nagios import NagiosError

import unittest


def mock_nrpe(cmd, shell=False, timeout=None):
    if 'check_load' in cmd:
        return 'OK - load average: 0.55, 0.38, 0.31|load1=0.550;15.000;20.000;0; load5=0.380;14.000;17.000;0; load15=0.310;12.000;15.000;0;'
    if 'check_disk' in cmd:
        return 'DISK OK - free space: / 1540 MB (16% inode=86%);| /=8026MB;8567;9373;0;10079'
    if 'check_mailq_postfix' in cmd:
        return 'WARNING: mailq is 1078 (threshold w = 10)|unsent=1078;10;5000;0'


def mock_ping(cmd, shell=False, timeout=None):
    return 'PING OK - Packet loss = 0%, RTA = 2.18 ms|rta=2.184000ms;5000.000000;5000.000000;0.000000 pl=0%;100;100;0'


def mock_snmp(cmd, shell=False, timeout=None):
    return 'OK - Ram: 42%, Cache: 11%, Swap: 0%  | ram_used=13872120;32816032;32816032;0;32816032 cache_used=29344352;32487872;32816032;0;32816032 swap_used=0;838860;2097150;0;4194300'


def mock_win(cmd, shell=False, timeout=None):
    if 'CheckCounter' in cmd:
        return "OK: ProcUsedMem: 1.00878e+009|'ProcUsedMem'=1008783360;1073741824;1073741824"
    if 'CheckCPU' in cmd:
        return "OK CPU Load ok.|'1'=7%;100;100 '5'=5%;100;100 '10'=6%;100;100"
    if 'CheckDriveSize' in cmd:
        return r"OK: C:\: 61.9G|'C:\ %'=62% 'C:\'=63425.141M"
    if 'CheckEventLog' in cmd:
        return "WinMgmt (2), Application Error (15), .NET Runtime (1), eventlog: 18 > critical|'eventlog'=18;1;1"
    if 'CheckFiles' in cmd:
        return "CheckFile ok|'found files'=0;0;1"
    if 'CheckLogFile' in cmd:
        return 'Nothing matched'
    if 'CheckMEM' in cmd:
        return "OK: physical memory: 4.76G, page file: 6.71G, virtual memory: 269M|'physical memory %'=29%;6;6 'physical memory'=4874.422M;15360;15360;0;16383.555 'page file %'=20%;53;53 'page file'=6869.602M;15360;15360;0;32765.301 'virtual memory %'=0%;99;99 'virtual memory'=268.777M;15360;15360;0;8388607.875"
    if 'CheckProcState' in cmd:
        return "OK: check_mk_agent.exe: running|'check_mk_agent.exe'=1;0;1"
    if 'CheckServiceState' in cmd:
        return 'OK: ENAIO_server: started'
    if 'CheckUpTime' in cmd:
        return "CRITICAL: uptime: 6d 17:29 < critical|'uptime'=581357000;86400000000;86400000000"


class TestNagios(unittest.TestCase):

    @patch('subprocess32.check_output', mock_nrpe)
    def test_nrpe(self):
        n = NagiosWrapper('test_host')
        result = n.nrpe('check_load')

        self.assertEquals(len(result), 3, 'Load check should return a dict with 3 items')
        self.assertIn('load1', result, 'Load check should contain load1 key')
        self.assertIn('load5', result, 'Load check should contain load5 key')
        self.assertIn('load15', result, 'Load check should contain load15 key')
        self.assertTrue(all(isinstance(v, float) for v in result.itervalues()),
                        'Load check should containt only float values')

        result = n.nrpe('check_disk', args=['/'])

        self.assertIn('/', result, 'Disk check should contain the mount key')
        self.assertEquals(8026000, result['/'], 'Disk check should contain the parsed value')

        result = n.nrpe('check_mailq_postfix')

        self.assertIn('unsent', result, 'Mail queue result should contain unsent messages')
        self.assertEquals(1078, result['unsent'], 'Mail queue check should contain the parsed value')

    @patch('subprocess32.check_output', mock_ping)
    def test_ping(self):
        n = NagiosWrapper('test_host')
        result = n.local('check_ping')

        self.assertEquals(len(result), 2, 'Ping check should return a dictionary with 2 items')
        self.assertIn('rta', result, 'Ping check should contain rta key')
        self.assertIn('pl', result, 'Ping check should conain pl key')

    @patch('subprocess32.check_output', mock_snmp)
    def test_snmp(self):
        n = NagiosWrapper('test_host')
        result = n.local('check_snmp_mem_used-cached.pl')

        self.assertEquals(len(result), 3, 'Snmp memory check should return a dictionary with 3 items')
        self.assertIn('ram_used', result, 'Snmp memory check should contain ram_used key')
        self.assertIn('cache_used', result, 'Snmp memory check should contain cache_used key')
        self.assertIn('swap_used', result, 'Snmp memory check should contain swap_used key')
        self.assertTrue(all(isinstance(v, float) for v in result.itervalues()),
                        'Snmp memory check check should containt only float values')

    @patch('subprocess32.check_output', mock_win)
    def test_win(self):
        n = NagiosWrapper('test_host')

        self.assertDictEqual(n.win('CheckCounter'), {'ProcUsedMem': 1008783360})
        self.assertDictEqual(n.win('CheckCPU'), {'1': 7, '10': 6, '5': 5})
        self.assertDictEqual(n.win('CheckDriveSize'), {'C:\\ %': 62.0, 'C:\\': 63425.141})
        self.assertDictEqual(n.win('CheckEventLog'), {'eventlog': 18})
        self.assertDictEqual(n.win('CheckFiles'), {'found files': 0})
        self.assertDictEqual(n.win('CheckLogFile'), {'count': 0})
        self.assertDictEqual(n.win('CheckMEM'), {
            'page file %': 20.0,
            'page file': 6869.602,
            'physical memory': 4874.422,
            'virtual memory': 268.777,
            'virtual memory %': 0.0,
            'physical memory %': 29.0,
        })
        self.assertDictEqual(n.win('CheckProcState'), {'status': 'OK', 'message': 'check_mk_agent.exe: running'})
        self.assertDictEqual(n.win('CheckServiceState'), {'status': 'OK', 'message': 'ENAIO_server: started'})
        self.assertDictEqual(n.win('CheckUpTime'), {'uptime': 581357000})

    def test_to_dict_commitdiff(self):
        r = \
            NagiosWrapper._to_dict_commitdiff('CheckDiff OK - CommitLimit-Committed_AS: 24801200 | 24801200;1048576;524288'
                                              )
        self.assertDictEqual({'CommitLimit-Committed_AS': 24801200}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_commitdiff('Error')

    def test_to_dict_logwatch(self):
        r = \
            NagiosWrapper._to_dict_logwatch('WARNING - 0 new of 109 Lines on /apache2/access.log|newlines=0;100;5000;0;'
                                            )
        self.assertDictEqual({'last': 0, 'total': 109}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_logwatch('Error')

    def test_to_dict_from_text(self):
        r = NagiosWrapper._to_dict_from_text('Status ERROR : Avis-File for Fiege is missing')
        self.assertDictEqual({'status': 'ERROR', 'message': 'Avis-File for Fiege is missing'}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_from_text('Error')

    def test_to_dict_iostat(self):
        r = \
            NagiosWrapper._to_dict_iostat('OK - IOread 0.00 kB/s, IOwrite 214.80 kB/s  on sda with  31.10 tps |ioread=0.00;32000;64000;0;iowrite=214.80;30000;40000;0;'
                                          )
        self.assertDictEqual({'ioread': 0.0, 'iowrite': 214.8, 'tps': 31.1}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_iostat('Error')

    def test_to_dict_hpraid(self):
        r = \
            NagiosWrapper._to_dict_hpraid('logicaldrive 1 (68.3 GB, RAID 1, OK) -- physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SAS, 146 GB, OK) -- physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SAS, 72 GB, OK) -- logicaldrive 2 (279.4 GB, RAID 1, OK) -- physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SAS, 300 GB, OK) -- physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SAS, 300 GB, OK) -- logicaldrive 3 (279.4 GB, RAID 1, OK) -- physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SAS, 300 GB, OK) -- physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SAS, 300 GB, OK) --'
                                          )
        self.assertDictEqual({
            'logicaldrive_1': 'OK',
            'logicaldrive_2': 'OK',
            'logicaldrive_3': 'OK',
            'physicaldrive_1I:1:1': 'OK',
            'physicaldrive_1I:1:2': 'OK',
            'physicaldrive_1I:1:3': 'OK',
            'physicaldrive_1I:1:4': 'OK',
            'physicaldrive_2I:1:5': 'OK',
            'physicaldrive_2I:1:6': 'OK',
        }, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_hpraid('Error')

    def test_to_dict_hpasm(self):
        r = \
            NagiosWrapper._to_dict_hpasm('''OK - ignoring 16 dimms with status 'n/a' , System: 'proliant dl360p gen8', S/N: 'CZJ2340R6C', ROM: 'P71 08/20/2012', hardware working fine, da: 1 logical drives, 4 physical drives'''
                                         )
        self.assertDictEqual({'message': "ignoring 16 dimms with status 'n/a' , System: 'proliant dl360p gen8', S/N: 'CZJ2340R6C', ROM: 'P71 08/20/2012', hardware working fine, da: 1 logical drives, 4 physical drives"
                             , 'status': 'OK'}, r)

    def test_parse_memory(self):
        r = NagiosWrapper._parse_memory('DISK OK - free space: / 1540 MB (16% inode=86%);| /=8026MB;8567;9373;0;10079')
        self.assertDictEqual({'/': 8026000}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._parse_memory('Error')

    def test_to_dict_win(self):
        r = \
            NagiosWrapper._to_dict_win("OK: physical memory: 4.76G, page file: 6.71G, virtual memory: 269M|'physical memory %'=29%;6;6 'physical memory'=4874.422M;15360;15360;0;16383.555 'page file %'=20%;53;53 'page file'=6869.602M;15360;15360;0;32765.301 'virtual memory %'=0%;99;99 'virtual memory'=268.777M;15360;15360;0;8388607.875"
                                       )
        self.assertDictEqual({
            'page file %': 20.0,
            'page file': 6869.602,
            'physical memory': 4874.422,
            'virtual memory': 268.777,
            'virtual memory %': 0.0,
            'physical memory %': 29.0,
        }, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_win('Error')

    def test_to_dict_win_text(self):
        r = NagiosWrapper._to_dict_win_text("OK: check_mk_agent.exe: running|'check_mk_agent.exe'=1;0;1")
        self.assertDictEqual({'status': 'OK', 'message': 'check_mk_agent.exe: running'}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_win_text('Error')

    def test_to_dict_win_log(self):
        r = NagiosWrapper._to_dict_win_log('Nothing matched')
        self.assertDictEqual({'count': 0}, r)
        with self.assertRaises(NagiosError):
            NagiosWrapper._to_dict_win_log('Error')


if __name__ == '__main__':
    unittest.main()
