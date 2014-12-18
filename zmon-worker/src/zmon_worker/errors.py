#!/usr/bin/env python
# -*- coding: utf-8 -*-


class CheckError(Exception):

    pass


class SecurityError(Exception):

    pass


class NagiosError(CheckError):

    def __init__(self, output):
        self.output = output
        super(NagiosError, self).__init__()

    def __str__(self):
        return 'NagiosError. Command output: {}'.format(self.output)


class InsufficientPermissionsError(CheckError):

    def __init__(self, user, entity):
        self.user = user
        self.entity = entity

    def __str__(self):
        return 'Insufficient permisions for user {} to access {}'.format(self.user, self.entity)


class SnmpError(CheckError):

    def __init__(self, message):
        self.message = message
        super(SnmpError, self).__init__()

    def __str__(self):
        return 'SNMP Error. Message: {}'.format(self.message)


class JmxQueryError(CheckError):

    def __init__(self, message):
        self.message = message
        super(JmxQueryError, self).__init__()

    def __str__(self):
        return 'JMX Query failed: {}'.format(self.message)


class HttpError(CheckError):

    def __init__(self, message, url=None):
        self.message = message
        self.url = url
        super(HttpError, self).__init__()

    def __str__(self):
        return 'HTTP request failed for {}: {}'.format(self.url, self.message)


class DbError(CheckError):

    def __init__(self, message, operation=None):
        self.message = message
        self.operation = operation
        super(DbError, self).__init__()

    def __str__(self):
        return 'DB operation {} failed: {}'.format(self.operation, self.message)


