#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pythonwhois


class WhoisWrapper(object):

    def __init__(self, host, timeout=10):
        self.host = host
        self.timeout = timeout

    def check(self):
        parsed = {}
        data, server_list = pythonwhois.net.get_whois_raw(self.host, with_server_list=True)
        if len(server_list) > 0:
            parsed = pythonwhois.parse.parse_raw_whois(data, normalized=True, never_query_handles=False,
                                                       handle_server=server_list[-1])
        else:
            parsed = pythonwhois.parse.parse_raw_whois(data, normalized=True)

        return parsed


if __name__ == '__main__':
    import json
    import sys
    import datetime


    def json_fallback(obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return obj


    data = WhoisWrapper(sys.argv[1]).check()
    print json.dumps(data, default=json_fallback, indent=4)
