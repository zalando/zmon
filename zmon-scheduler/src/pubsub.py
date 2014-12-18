#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import traceback
import redis
from redis_context_manager import RedisConnHandler

from threading import Thread


class Subscriber(object):

    PUBSUB_KILL_MSG = 'zmon:pubsub:kill'

    def __init__(self, config, callback, pubsub_channel, message_exchange):
        '''
        Creates a new instance of Subscriber. The subscriber object takes care of maintaining pubsub connection with
        redis and listens for incoming messages. Whenever a new message is received, the subscriber will try to fetch,
        parse the response and call the callback with the result.
        Parameters
        ----------
        config: dict
            Configuration dict that must contain 'backend' key for configuring redis connection.
        callback: Callable
            A callback that will be called with data received over pubsub channel.
        pubsub_channel: str
            Name of the pubsub channel.
        message_exchange: str
            Name of the message exchange.
        '''

        self.callback = callback
        self.pubsub_channel = pubsub_channel
        self.message_exchange = message_exchange
        self.logger = logging.getLogger('zmon-scheduler')
        self.pubsub_initialized = False
        self.__init_pubsub()

    def __init_pubsub(self):
        try:
            with RedisConnHandler.get_instance() as ch:
                self.redis = ch.get_conn()
                self.pubsub = self.redis.pubsub()
                self.pubsub.subscribe(self.pubsub_channel)
            self.listen_thread = Thread(target=self._listen, name='subscriber_listen_thread')
            self.listen_thread.daemon = True
        except Exception:
            self.logger.warn('Error initializing pubsub channel. Exception: %s', traceback.format_exc())
        else:
            self.pubsub_initialized = True
            self.listen_thread.start()

    def __kill_pubsub(self):
        self.redis.publish(self.pubsub_channel, self.PUBSUB_KILL_MSG)

    def _listen(self):
        # PF-3517 If redis dies after establishing pubsub channel, we will get a ConnectionError while listening. This
        # is very unlikely, but already happened once.
        try:
            for item in self.pubsub.listen():
                request_id = item['data']

                if request_id == self.PUBSUB_KILL_MSG:
                    break

                try:
                    request = json.loads(self.redis.hget(self.message_exchange, request_id) or 'null')
                except ValueError:
                    self.logger.warn('Error while parsing pubsub JSON with request ID: %s', request_id)
                else:
                    if request is None:
                        self.logger.warn('No pubsub request for id: %s', request_id)
                    else:
                        self.callback(request)
        except redis.ConnectionError:
            self.logger.warn('Lost pubsub connection.')
            self.pubsub_initialized = False

    def check_status(self):
        '''
        This method should be called periodically to check it the pubsub connection is still alive. The listen thread
        is blocking, so if something happens to redis after establishing pubsub connection, but while listening, the
        thread will get an exception. This method will check pubsub's status and reinitialise it if needed.
        '''

        if not self.pubsub_initialized:
            self.__init_pubsub()

    def unsubscribe(self):
        '''
        Closes the pubsub channel and terminates the listen thread.
        '''

        self.__kill_pubsub()
        try:
            self.pubsub.unsubscribe()
        except Exception:
            self.logger.warn('Unsubscribe error', exc_info=True)
        else:
            self.pubsub_initialized = False


