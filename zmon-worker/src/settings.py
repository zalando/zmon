# -*- coding: utf-8 -*-

"""
Project settings:
 To customize the settings for a local environment please create another module called settings_local.py and change
 there the values you want.

You don't have to duplicate all the logic in settings_dev.py inside settings_local.py, instead you import it and
can modify certain values from settings_dev. For example to modify only the log level:

##### content of file: settings_local.py

from settings_dev import *
LOGGING['loggers']['']['level'] = 'INFO'
RPC_SERVER_CONF['LOGGING']['loggers']['']['level'] = 'INFO'

#### END of settings_local.py
"""


EXTERNAL_CONFIG = {}


try:
    from settings_local import *
except ImportError:
    # no settings_local.py found, falling back to settings_pro.py
    from settings_pro import *


def set_workers_log_level(level):
    if level:
        LOGGING['loggers']['']['level'] = level


def set_rpc_server_port(port):
    if port and str(port).isdigit():
        RPC_SERVER_CONF['PORT'] = int(port)


def set_external_config(external_config):
    global EXTERNAL_CONFIG
    EXTERNAL_CONFIG = dict(external_config)


def get_external_config():
    return EXTERNAL_CONFIG
