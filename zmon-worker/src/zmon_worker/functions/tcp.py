#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from contextlib import closing


class TcpWrapper(object):

    def __init__(self, host, timeout=10):
        self.host = host
        self.timeout = timeout

    def open(self, *ports):
        results = {}
        for port in ports:
            with closing(socket.socket()) as s:
                s.settimeout(self.timeout)
                try:
                    s.connect((self.host, port))
                except Exception, e:
                    results[port] = str(e)
                else:
                    results[port] = 'OK'
        if len(ports) == 1:
            return results[ports[0]]
        else:
            return results

    def resolve(self, host):
        try:
            result = socket.gethostbyname(host)
        except Exception, e:
            result = 'ERROR: ' + str(e)
        return result


if __name__ == '__main__':
    import sys
    tcp = TcpWrapper(sys.argv[1])
    print tcp.open(22, 80, 123)
    print tcp.open(22)
