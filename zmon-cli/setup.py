#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Setup file for zmon_cli.
"""

import os
import inspect

import setuptools
from setuptools import setup

__location__ = os.path.join(os.getcwd(), os.path.dirname(inspect.getfile(inspect.currentframe())))


def read_version(package):
    data = {}
    with open(os.path.join(package, '__init__.py'), 'r') as fd:
        exec(fd.read(), data)
    return data['__version__']

NAME = 'zmon-cli'
MAIN_PACKAGE = 'zmon_cli'
VERSION = read_version(MAIN_PACKAGE)
DESCRIPTION = 'ZMON CLI'
CONSOLE_SCRIPTS = ['zmon = zmon_cli.main:main']


def get_install_requirements(path):
    content = open(os.path.join(__location__, path)).read()
    return [req for req in content.split('\\n') if req != '']


def read(fname):
    return open(os.path.join(__location__, fname)).read()


def setup_package():

    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        keywords='zmon command line interface',
        test_suite='tests',
        packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
        install_requires=get_install_requirements('requirements.txt'),
        entry_points={'console_scripts': CONSOLE_SCRIPTS},
    )


if __name__ == '__main__':
    setup_package()
