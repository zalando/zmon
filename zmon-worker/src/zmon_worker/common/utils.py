#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dogpile.cache import make_region
import threading
from functools import wraps
import sys
import os
import time
import random

DEFAULT_CACHE_EXPIRATION_TIME = 3600


def get_cache_file_path():
    cache_filename = 'worker_cache.dbm'
    app_folder = (os.environ['APP_HOME'] if 'APP_HOME' in os.environ else os.getcwd())
    cache_dir = (os.path.join(app_folder, 'temp') if os.path.isdir(os.path.join(app_folder, 'temp')) else app_folder)
    return os.path.join(cache_dir, cache_filename)


def async_creation_runner(cache, somekey, creator, mutex):
    ''' Used by dogpile.core:Lock when appropriate '''

    def runner():
        try:
            value = creator()
            cache.set(somekey, value)
        finally:
            mutex.release()

    thread = threading.Thread(target=runner)
    thread.start()


# Asynchronous cache decorator persisted to memory.
# After the first successful invocation cache updates happen in a background thread.
async_memory_cache = make_region(async_creation_runner=async_creation_runner).configure('dogpile.cache.memory',
        expiration_time=DEFAULT_CACHE_EXPIRATION_TIME)


def with_retries(max_retries=5, delay=5):
    ''' A helper decorator to handle retries on function call failures '''

    def decorator(f):

        random_delta = 0.25  # percent of random deviation we will introduce in waiting time

        @wraps(f)
        def wrapper(*args, **kwargs):
            retry, ts = 0, delay
            while True:
                try:
                    return f(*args, **kwargs)
                except Exception, e:
                    if retry >= max_retries:
                        traceback = sys.exc_info()[2]
                        raise Exception('Max retries exceeded. Internal error: {}'.format(e)), None, traceback
                    time.sleep(ts + random.uniform(-ts, ts) * random_delta)
                    retry += 1
                    ts *= 2  # duplicate waiting time
        return wrapper

    return decorator


