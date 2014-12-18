#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Client module for connecting to an rpc_server in a remote machine

Test of execution:
python rpc_client.py http://localhost:8000/patata popo_method int:3.5  float:5.6
"""

import sys
import xmlrpclib

DEBUG = True

_cmd_struct = {
    'endpoint': None,
    'method_name': None,
    'args': []
}


def parse_cmd_line(args):

    admitted_types = ('int', 'float', 'str')

    cmd_parts = dict(_cmd_struct)
    cmd_parts['endpoint'] = args[1]
    cmd_parts['method_name'] = args[2]
    cmd_parts['args'] = []

    raw_method_args = args[3:]

    for raw_arg in raw_method_args:

        #arg_parts = raw_arg.strip('"\'').split(':')
        arg_parts = raw_arg.split(':')

        if len(arg_parts) == 1 or arg_parts[0] not in admitted_types:
            arg_type, arg_value = 'str', ':'.join(arg_parts[0:])
            if arg_value.isdigit():
                arg_type = 'int'
            elif not (arg_value.startswith('.') or arg_value.endswith('.')) and arg_value.replace('.', '', 1).isdigit():
                arg_type = 'float'
        else:
            arg_type, arg_value = arg_parts[0], ':'.join(arg_parts[1:])

        try:
            value = eval('{0}({1})'.format(arg_type, arg_value)) if arg_type != 'str' else arg_value
        except Exception:
            print >> sys.stderr, "\n Error: Detected argument with wrong format"
            sys.exit(3)

        cmd_parts['args'].append(value)

    return cmd_parts


def get_rpc_client(endpoint):
    """
    Get an rpc client object to remote server listening at endpoint
    :param endpoint: http://host:port/rpc_path
    :return: rpc_client object
    """
    return xmlrpclib.ServerProxy(endpoint)


if __name__ == '__main__':

    if len(sys.argv) <= 2:
        print >>sys.stderr, 'usage: {0} http://<host>:<port>/<rpc_path> <method_name> [ [int|float|str]:arg1 ' \
                            '[int|float|str]:arg2 ...[int|float|str]:argN ...]'.format(sys.argv[0])
        sys.exit(1)

    cmd_line = parse_cmd_line(sys.argv[:])

    if DEBUG:
        print 'Parsed cmd_line: ', cmd_line

    client = get_rpc_client(cmd_line['endpoint'])

    #Executing now the remote method
    result = getattr(client, cmd_line['method_name'])(*cmd_line['args'])
    if result is not None:
        print ">>Result:\n", result
