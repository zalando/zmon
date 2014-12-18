#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zmon_worker.errors import SnmpError
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import Integer, OctetString, Counter32, Counter64
import re
import subprocess32


class SnmpWrapper(object):

    def __init__(self, host, community='public', version='v2c', timeout=5):
        if re.match(r'^[0-9]+$', str(timeout)):
            self.timeout = timeout
        if re.match(r'^[\w\-.]+$', host):
            self.host = host
        self.generator = cmdgen.CommandGenerator()
        self.transport = cmdgen.UdpTransportTarget((host, 161), timeout=timeout)
        if version == 'v2c':
            # self.comm_data = cmdgen.CommunityData('server', community, 1)  # 1 means version SNMP v2c
            self.comm_data = cmdgen.CommunityData(community)

    def memory(self):
        '''return {'free': 3, ..}
        # 3 UCD-SNMP-MIB::memTotalSwap.0 = INTEGER: 4194300 kB
        # 4 UCD-SNMP-MIB::memAvailSwap.0 = INTEGER: 4194300 kB
        # 5 UCD-SNMP-MIB::memTotalReal.0 = INTEGER: 32816032 kB
        # 6 UCD-SNMP-MIB::memAvailReal.0 = INTEGER: 9392600 kB
        # 11 UCD-SNMP-MIB::memTotalFree.0 = INTEGER: 13586900 kB
        # 12 UCD-SNMP-MIB::memMinimumSwap.0 = INTEGER: 16000 kB
        # 13 UCD-SNMP-MIB::memShared.0 = INTEGER: 0 kB
        # 14 UCD-SNMP-MIB::memBuffer.0 = INTEGER: 299992 kB
        # 15 UCD-SNMP-MIB::memCached.0 = INTEGER: 6115656 kB
        '''

        result = {}
        oids = {
            'swap_total': '1.3.6.1.4.1.2021.4.3.0',
            'swap_free': '1.3.6.1.4.1.2021.4.4.0',
            'ram_total': '1.3.6.1.4.1.2021.4.5.0',
            'ram_free': '1.3.6.1.4.1.2021.4.6.0',
            'ram_total_free': '1.3.6.1.4.1.2021.4.11.0',
            'swap_min': '1.3.6.1.4.1.2021.4.12.0',
            'ram_shared': '1.3.6.1.4.1.2021.4.13.0',
            'ram_buffer': '1.3.6.1.4.1.2021.4.14.0',
            'ram_cache': '1.3.6.1.4.1.2021.4.15.0',
        }
        for k, oid in oids.items():
            val = self._get_cmd(oid)
            result[k] = self.parse(Integer, int, val)
        return result

    def load(self):
        '''
        Return CPU Load Averages
        Example result: {"load1":0.95,"load5":0.69,"load15":0.72}
        '''

        result = {}
        oids = {'load1': '1.3.6.1.4.1.2021.10.1.3.1', 'load5': '1.3.6.1.4.1.2021.10.1.3.2',
                'load15': '1.3.6.1.4.1.2021.10.1.3.3'}
        for k, oid in oids.items():
            val = self._get_cmd(oid)
            result[k] = self.parse(OctetString, lambda x: float(str(x)), val)
        return result

    def cpu(self):
        '''
        Returns CPU Percentage

        Example result: {"cpu_system":0,"cpu_user":19,"cpu_idle":79}
        '''

        result = {}
        oids = {'cpu_idle': '1.3.6.1.4.1.2021.11.11.0', 'cpu_user': '1.3.6.1.4.1.2021.11.9.0',
                'cpu_system': '1.3.6.1.4.1.2021.11.10.0'}
        for k, oid in oids.items():
            val = self._get_cmd(oid)
            result[k] = self.parse(Integer, int, val)
        return result

    def cpu_raw(self):
        result = {}
        oids = {
            'raw_cpu_user': '1.3.6.1.4.1.2021.11.50.0',
            'raw_cpu_system': '.1.3.6.1.4.1.2021.11.52.0',
            'raw_cpu_nice': '.1.3.6.1.4.1.2021.11.51.0',
            'raw_cpu_idle': '.1.3.6.1.4.1.2021.11.53.0',
        }
        for k, oid in oids.items():
            val = self._get_cmd(oid)
            result[k] = self.parse(Counter32, int, val)
        return result

    def df(self):
        '''
        Return disk usage information

        Example result: {"/data/postgres-wal-nfs-itr":{"percentage_space_used":0,"used_space":160,"total_size":524288000,"device":"zala0-1-stp-02:/vol/zal_pgwal","available_space":524287840,"percentage_inodes_used":0}}
        '''

        # disk_table = '.1.3.6.1.4.1.2021.9'
#        base = '1.3.6.1.4.1.2021.13.15.1.1'
        base = '1.3.6.1.4.1.2021.9.1'
        base_idx = base + '.1.'
        base_name = base + '.2.'
        results = {}
        idx2name = {}
        result_all = self._get_walk(base)
        for oid in sorted(result_all.keys()):
            if base_idx in oid:
                val = str(result_all[oid])
                idx2name[val] = None
            elif base_name in oid:
                idx = oid.split('.')[-1]
                val = result_all[oid]
                idx2name[idx] = val
        for oid in sorted(result_all.keys()):
            if oid in base_idx or oid in base_name:
                continue
            idx = oid.split('.')[-1]
            name = str(idx2name[idx])
            if 'loop' in name or 'ram' in name:
                continue
            results[name] = results.get(name, {})
            tname = oid
            kind = oid.split('.')[-2]
            if kind == '3':
                tname = 'device'
            elif kind == '6':
                tname = 'total_size'  # kBytes
            elif kind == '7':
                tname = 'available_space'  # kBytes
            elif kind == '8':
                tname = 'used_space'  # kBytes
            elif kind == '9':
                tname = 'percentage_space_used'
            elif kind == '10':
                tname = 'percentage_inodes_used'
            elif kind == '11':
                tname = 'total_size'  # Gauge32
            elif kind == '13':
                tname = 'available_space'  # Gauge32
            elif kind == '15':
                tname = 'used_space'  # Gauge32
            else:
                continue
            results[name][tname] = result_all[oid]
        return results

    def logmatch(self):
        # logmatch_table = '.1.3.6.1.4.1.2021.16'
        base = '1.3.6.1.4.1.2021.16.2.1'
        base_idx = base + '.1.'
        base_name = base + '.2.'
        results = {}
        idx2name = {}
        result_all = self._get_walk(base)
        for oid in sorted(result_all.keys()):
            if base_idx in oid:
                val = str(result_all[oid])
                idx2name[val] = None
            elif base_name in oid:
                idx = oid.split('.')[-1]
                val = result_all[oid]
                idx2name[idx] = val
        for oid in sorted(result_all.keys()):
            if oid in base_idx or oid in base_name:
                continue
            idx = oid.split('.')[-1]
            name = str(idx2name[idx])
            results[name] = results.get(name, {})
            tname = oid
            kind = oid.split('.')[-2]
            if kind == '3':
                tname = 'file'  # file name
            elif kind == '4':
                tname = 'regex'  # regex string
            elif kind == '5':
                tname = 'global_count'  # counter32
            elif kind == '7':
                tname = 'current_count'  # counter32 since last logrotation
            elif kind == '9':
                tname = 'last_count'  # counter32 since last read
            else:
                continue
            results[name][tname] = result_all[oid]
        return results

    def interfaces(self):
        # IF-MIB::interfaces_table = '1.3.6.1.2.1.2.'
        # IF-MIB::ifMIB_table = '1.3.6.1.2.1.31'
        base = '1.3.6.1.2.1.2.2.1'
        base_idx = base + '.1.'
        base_name = base + '.2.'
        results = {}
        idx2name = {}
        result_all = self._get_walk(base)
        for oid in sorted(result_all.keys()):
            if base_idx in oid:
                val = str(result_all[oid])
                idx2name[val] = None
            elif base_name in oid:
                idx = oid.split('.')[-1]
                val = result_all[oid]
                idx2name[idx] = val
        for oid in sorted(result_all.keys()):
            if oid in base_idx or oid in base_name:
                continue
            idx = oid.split('.')[-1]
            name = str(idx2name[idx])
            results[name] = results.get(name, {})
            tname = oid
            kind = oid.split('.')[-2]
            if kind == '7':
                tname = 'opStatus'  # operational status
            elif kind == '8':
                tname = 'adStatus'  # administratal status
            elif kind == '13':
                tname = 'in_discards'  # counter32
            elif kind == '14':
                tname = 'in_error'  # counter32
            elif kind == '19':
                tname = 'out_discards'  # counter32
            elif kind == '20':
                tname = 'out_error'  # counter32
            else:
                continue
            results[name][tname] = result_all[oid]

        # IF-MIB::ifMIB_table = '1.3.6.1.2.1.31'
        base = '1.3.6.1.2.1.31.1.1.1'
        base_idx = '1.3.6.1.2.1.2.2.1.1.'
        base_name = base + '.1.'
        # results = {}
        idx2name = {}
        result_all = self._get_walk(base)
        for oid in sorted(result_all.keys()):
            if base_idx in oid:
                val = str(result_all[oid])
                idx2name[val] = None
            elif base_name in oid:
                idx = oid.split('.')[-1]
                val = result_all[oid]
                idx2name[idx] = val
        for oid in sorted(result_all.keys()):
            if oid in base_idx or oid in base_name:
                continue
            idx = oid.split('.')[-1]
            name = str(idx2name[idx])
            results[name] = results.get(name, {})
            tname = oid
            kind = oid.split('.')[-2]
            if kind == '6':
                tname = 'in_octets'  # counter64
            elif kind == '10':
                tname = 'out_octets'  # counter64
            elif kind == '15':
                tname = 'speed'  # gauge32
            else:
                continue
            results[name][tname] = result_all[oid]
        return results

    def postgres_backup(self):
        # val = self._get_mib('public', 'NET-SNMP-EXTEND-MIB', 'check_postgres_backup')
        # res = self.parse(OctetString, str, val)
        # Workaround for a too large check response from the script(too large udp packets are blocked by the fw, so we use tcp)
        cmd = \
            '/usr/bin/snmpget -v2c -c public -t {timeout} tcp:{host} \'NET-SNMP-EXTEND-MIB::nsExtendOutputFull."check_postgres_backup"\''.format(timeout=self.timeout,
                host=self.host)
        try:
            output = subprocess32.check_output(cmd, shell=True, timeout=self.timeout, stderr=subprocess32.STDOUT)
        except subprocess32.CalledProcessError, e:
            database_backup_size, warnings, check_duration = {}, [str(e.output)], 0
        else:
            res = output.partition(': ')[2]
            s = res.split('|')
            warning = s[0]
            perfdata = s[-1]
            database_backup_size = {}
            check_duration = 0
            for pd in perfdata.split(' '):
                k, _, v = pd.partition('=')
                v = v.split(';')[0]
                if k == 'time':
                    check_duration = v
                else:
                    database_backup_size[k] = v
            warnings = warning.split(';')
        return {'database_backup_size': database_backup_size, 'warnings': warnings, 'check_duration': check_duration}

    def disk_pgxlog(self):
        result = {}
        output = str(self._get_mib('public', 'NET-SNMP-EXTEND-MIB', 'disk_pgxlog'))
        output = [i for i in re.split('\s{1,}|\t|\n', output) if i.isdigit() or i.startswith('/')]
        output = [output[i:i + 7] for i in range(0, len(output), 7)]
        output = [[
            i[1],
            int(int(i[0]) / 1024),
            i[2],
            int(i[3]),
            int(i[4]),
            int(i[5]),
            i[6],
        ] for i in output]
        for i in output:
            name = str(i[0])
            result[name] = {}
            for index in range(len(i)):
                val = i[index]
                if val == i[1]:
                    tname = 'du_dir'
                elif val == i[2]:
                    tname = 'filesystem'
                elif val == i[3]:
                    tname = 'totalspace'
                elif val == i[4]:
                    tname = 'used_space'
                elif val == i[5]:
                    tname = 'available_space'
                elif val == i[6]:
                    tname = 'mounted_on'
                else:
                    continue
                result[name][tname] = i[index]

        return result

    def conntrackstats(self):
        output = str(self._get_mib('public', 'NET-SNMP-EXTEND-MIB', 'conntrackstats'))
        return dict((a.split('=')[0].strip(), int(a.split('=')[1])) for a in output.split('|'))

    #
    # snmp functions
    #

    def get_list(self, prefix='get', convert=int, *oids):
        h = {}
        for idx, oid in enumerate(oids):
            k = '{0}{1}'.format(prefix, idx)
            h[k] = self.get(oid, k, convert)
        return h

    def get(self, oid, name, convert):
        '''Example:
        get('1.3.6.1.4.1.2021.4.6.0', 'foo', int) -> {'foo': 42}
        '''

        val = self._get_cmd(oid)
        result = convert(val)
        return {name: result}

    def _get_mib(self, community, prefix, extend, mib_result='nsExtendOutputFull', path=None):
        '''Parameter: mib_result can be 'nsExtendOutputFull', 'nsExtendResult', ..
        Example:
        _get_mib("public", "NET-SNMP-EXTEND-MIB", "check_postgres_backup")
        is the same like:
        % snmpget -v2c -c public z-storage02 'NET-SNMP-EXTEND-MIB::nsExtendOutputFull."check_postgres_backup"'
        '''

        mib = None
        if path:
            mib = cmdgen.MibVariable(prefix, mib_result, extend).addMibSource(path)
        else:
            mib = cmdgen.MibVariable(prefix, mib_result, extend)
        real_fun = getattr(self.generator, 'getCmd')  # SNMPGET
        res = errorIndication, errorStatus, errorIndex, varBinds = real_fun(self.comm_data, self.transport, mib)

        if not errorIndication is None or errorStatus is True:
            msg = 'Error: %s %s %s %s' % res
            raise SnmpError(msg)
        else:
            _, val = varBinds[0]
            return val

    def _get_mib_bulkwalk(self, community, prefix, table, path=None):
        '''
        % snmpbulkwalk -v2c -c public myhost123 TCP-MIB::tcpConnTable
        '''

        mib = None
        if path:
            mib = cmdgen.MibVariable(prefix, table).addMibSource(path)
        else:
            mib = cmdgen.MibVariable(prefix, table)
        real_fun = getattr(self.generator, 'bulkCmd')  # SNMPBULKWALK
        res = errorIndication, errorStatus, errorIndex, varBinds = real_fun(self.comm_data, self.transport, 0, 50, mib,
                max_rows=100, ignore_non_increasing_oid=True)

        if not errorIndication is None or errorStatus is True:
            msg = 'Error: %s %s %s %s' % res
            raise SnmpError(msg)
        else:
            res = {}
            for items in varBinds:
                oid = str(items[0][0])
                val = items[0][1]
                if isinstance(val, Counter64) or isinstance(val, Counter32) or isinstance(val, Integer):
                    res[oid] = int(val)
                else:
                    res[oid] = str(val)
            return res

    def _get_walk(self, oid):
        '''Returns a dictionary of oid -> value'''

        real_fun = getattr(self.generator, 'nextCmd')  # SNMPWALK
        res = errorIndication, errorStatus, errorIndex, varBinds = real_fun(self.comm_data, self.transport, oid)
        if not errorIndication is None or errorStatus is True:
            msg = 'Error: %s %s %s %s' % res
            raise SnmpError(msg)
        else:
            res = {}
            for items in varBinds:
                oid = str(items[0][0])
                val = items[0][1]
                if isinstance(val, Counter64) or isinstance(val, Counter32) or isinstance(val, Integer):
                    res[oid] = int(val)
                else:
                    res[oid] = str(val)
            return res

    def _get_cmd(self, oid):
        real_fun = getattr(self.generator, 'getCmd')  # SNMPGET
        res = errorIndication, errorStatus, errorIndex, varBinds = real_fun(self.comm_data, self.transport, oid)

        if not errorIndication is None or errorStatus is True:
            msg = 'Error: %s %s %s %s' % res
            raise SnmpError(msg)
        else:
            _, val = varBinds[0]
            return val

    # Convert SNMP data to python data
    def parse(self, clazz, convert, val):
        '''Example: self.parse(Integer, int, Integer(11040956))'''

        if not val:
            return None
        if isinstance(val, clazz):
            return convert(val)
        raise SnmpError('Could not convert [{}] with {} into {}'.format(val, convert, clazz))


