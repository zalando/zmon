# -*- coding: utf-8 -*-
"""
Project settings for development:
 To customize the settings for a local environment please create another module called settings_local.py and change
 there the values you want, they will override the ones in this file
"""

import os


get_log_path = lambda: os.path.join(os.environ['APP_HOME'], 'logs') if 'APP_HOME' in os.environ else './'



app_home = os.path.abspath(os.environ['APP_HOME'] if 'APP_HOME' in os.environ else './')

data_dir = os.path.abspath(os.path.join(app_home, 'zmon_worker_data'))

#_LOG_DIR = os.path.abspath(os.path.join(app_home, 'logs'))


# application data folder needs to be created by the application itself
for d in (data_dir, get_log_path()):
    if not os.path.isdir(d):
        os.mkdir(d)



#Log configuration for the workers

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
            'level': 'DEBUG',
            'filename': os.path.join(get_log_path(), _LOG_MAIN_FILENAME),
            'class': 'logging.FileHandler',
            'formatter': 'custom'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'custom'
        },
        'rot_file': {
            'level': 'DEBUG',
            'filename': os.path.join(get_log_path(), _LOG_MAIN_FILENAME),
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
            'level': 'DEBUG',
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
                'level': 'DEBUG',
                'filename': os.path.join(get_log_path(), _LOG_RPC_SERVER_FILENAME),
                'class': 'logging.FileHandler',
                'formatter': 'custom'
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'custom'
            },
            'rot_file': {
                'level': 'DEBUG',
                'filename': os.path.join(get_log_path(), _LOG_RPC_SERVER_FILENAME),
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
                'level': 'DEBUG',
                },
            }
    }
)

