# -*- coding: utf-8 -*-
"""
Project settings for development:
 To customize the settings for a local environment please create another module called settings_local.py and change
 there the values you want, they will override the ones in this file
"""

import os

src_dir_path = os.path.abspath(os.path.dirname(__file__))

data_dir = os.path.abspath(os.path.join(src_dir_path, '../data'))

# the old zmon2 worker config is taken from the user home folder
zmon_worker_config_file = os.path.expanduser('~/.zmon-worker.conf')


### Some sanity checks for easy diagnostic
assert os.path.isdir(data_dir), "zmon worker configured data not found: {}".format(data_dir)
assert os.path.isfile(zmon_worker_config_file), "zmon worker config file must be placed at {}".format(zmon_worker_config_file)


#Log folder of the project
_LOG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs'))

_LOG_MAIN_FILENAME = 'worker_{pid}.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
        },
        'custom': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
        },
    },

    'handlers': {
        'file': {
            'level': 'INFO',
            'filename': os.path.join(_LOG_ROOT, _LOG_MAIN_FILENAME),
            'class': 'logging.FileHandler',
            'formatter': 'custom'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'custom'
        },
        'rot_file': {
            'level': 'INFO',
            'filename': os.path.join(_LOG_ROOT, _LOG_MAIN_FILENAME),
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5242880,
            'backupCount': 10,
            'formatter': 'custom'
        },
    },

    'loggers': {
        '': {
            'handlers': ['rot_file', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
    }
}

#Log filename for the xmlrpcserver
_LOG_RPC_SERVER_FILENAME = 'rpc_server.log'

RPC_SERVER_CONF = dict(

    HOST='localhost',

    PORT=8500,

    RPC_PATH='/zmon_rpc',

    LOGGING={
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
            },
            'custom': {
                'format': '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
            },
            },

        'handlers': {
            'file': {
                'level': 'INFO',
                'filename': os.path.join(_LOG_ROOT, _LOG_RPC_SERVER_FILENAME),
                'class': 'logging.FileHandler',
                'formatter': 'custom'
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'custom'
            },
            'rot_file': {
                'level': 'INFO',
                'filename': os.path.join(_LOG_ROOT, _LOG_RPC_SERVER_FILENAME),
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 5242880,
                'backupCount': 10,
                'formatter': 'custom'
            },
            },

        'loggers': {
            '': {
                'handlers': ['rot_file', 'console'],
                'propagate': True,
                'level': 'INFO',
                },
            }
    }
)

