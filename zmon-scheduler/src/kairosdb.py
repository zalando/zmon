import time
import requests
import json

__logger = None

def setLogger(l):
    global __logger
    __logger = l

__host = 'localhost'
__port = '37629'
__env = 'integration'

def setKairosDB(host,port,env):
    global __host,__port,__env
    __host = host
    __port = port
    __env = env

def flatten(structure, key='', path='', flattened=None):
    path = str(path)
    key = str(key)

    if flattened is None:
        flattened = {}
    if type(structure) not in (dict, list):
        flattened[((path + '.' if path else '')) + key] = structure
    elif isinstance(structure, list):
        pass
    else:
        for new_key, value in structure.items():
            flatten(value, new_key, '.'.join(filter(None, [path, key])), flattened)
    return flattened


def get_kairosdb_value(name, time, value, tags):
    tags['env'] = __env
    r = {'name': name, 'datapoints': [[int(time * 1000), value]], 'tags': tags}
    return r

def write_to_kairosdb(values):
    try:
        r = requests.post('http://{}:{}/api/v1/datapoints'.format(__host,__port), json.dumps(values), timeout=5)

        if not r.status_code in [200, 204]:
            __logger.error(r.text)
            __logger.error(json.dumps(values))

    except Exception, e:
        __logger.error('KairosDB write failed {}'.format(e))
