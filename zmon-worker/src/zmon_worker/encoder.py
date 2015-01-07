#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import numpy

from collections import Set
from decimal import Decimal

class JsonDataEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        elif isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, Set):
            return list(o)
        elif isinstance(o, numpy.bool_):
            return bool(o)
        else:
            return super(JsonDataEncoder, self).default(o)

    def iterencode(self, o, _one_shot=False):
        for chunk in super(JsonDataEncoder, self).iterencode(o, _one_shot=_one_shot):
            yield {'NaN': 'null', 'Infinity': '"Infinity"', '-Infinity': '"-Infinity"'}.get(chunk, chunk)


if __name__ == '__main__':

    the_encoder = JsonDataEncoder()

    print repr(the_encoder.encode(numpy.nan))
    print repr(the_encoder.encode(numpy.Infinity))
    print repr(the_encoder.encode(-numpy.Infinity))
    print repr(the_encoder.encode([numpy.nan, numpy.Infinity, -numpy.Infinity]))
    print repr(the_encoder.encode({'NaN': numpy.nan, 'Infinity': numpy.Infinity, '-Infinity': -numpy.Infinity}))
