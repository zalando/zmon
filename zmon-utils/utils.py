#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from redis import StrictRedis

import logging

logging.basicConfig()
logger = logging.getLogger('zmon-utils')


def delete_redis_keys(args):
    r = StrictRedis(args.host, args.port or 6379)
    logger.info('Deleted %s keys', r.delete(*r.keys('zmon:*')))


if __name__ == '__main__':
    parser = ArgumentParser(description='Zmon utils')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity level')
    group.add_argument('-q', '--quiet', action='store_true', help='Decrease verbosity level')

    subparsers = parser.add_subparsers(title='Commands', description='Allowed commands')

    redis_parser = subparsers.add_parser('delete_keys',
                                         help='Delete redis keys. If no host is provided, integration will be used')
    redis_parser.add_argument('--host', help='Redis instance')
    redis_parser.add_argument('--port', help='Redis port')
    redis_parser.set_defaults(func=delete_redis_keys)

    args = parser.parse_args()

    loglevel = logging.INFO

    if args.quiet:
        loglevel = logging.WARN
    if args.verbose:
        loglevel = logging.DEBUG

    logger.setLevel(loglevel)

    args.func(args)
