#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess


def ping(host, count=1, timeout=1):
    cmd = [
        'ping',
        '-c',
        str(count),
        '-w',
        str(timeout),
        host,
    ]

    sub = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    sub.communicate()
    ret = sub.wait() == 0
    return ret


if __name__ == '__main__':
    import sys
    print ping(sys.argv[1])
