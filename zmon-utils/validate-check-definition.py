#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import ast
import logging
import sys

LOGGER = None

RESULT_OK = 0
RESULT_VALIDATION_ISSUES = 1
RESULT_VALIDATION_FAILED = 2
RESULT_ERRORS = 3

NOT_SET = object()

MANDATORY_FIELDS = set([
    'name',
    'description',
    'entities',
    'interval',
    'command',
    'status',
])

OPTIONAL_FIELDS = set(['technical_details', 'potential_analysis', 'potential_impact', 'potential_solution'])

STATUSES = ['ACTIVE', 'INACTIVE', 'REJECTED']
MAX_NAME_LENGTH = 256
MAX_INTERVAL = 2 ** 63 - 1
ALLOWED_GLOBALS = set([
    'abs',
    'all',
    'any',
    'avg',
    'basestring',
    'bin',
    'bool',
    'chain',
    'chr',
    'Counter',
    'dict',
    'divmod',
    'Exception',
    'empty',
    'enumerate',
    'entity',
    'eventlog',
    'exacrm',
    'exceptions',
    'False',
    'filter',
    'float',
    'groupby',
    'hex',
    'http',
    'int',
    'isinstance',
    'jmx',
    'jobs',
    'job_locks',
    'json',
    'ldap',
    'len',
    'list',
    'long',
    'map',
    'max',
    'min',
    'mysql',
    'nagios',
    'None',
    'normalvariate',
    'oct',
    'orasql',
    'ord',
    'ping',
    'pow',
    'range',
    'redis',
    'reduce',
    'reversed',
    'round',
    'set',
    'shop_frontend',
    'snmp',
    'soap',
    'sorted',
    'sql',
    'str',
    'sum',
    'tcp',
    'time',
    'True',
    'Try',
    'tuple',
    'unicode',
    'unichr',
    'whois',
    'xrange',
    'zip',
    'zmon',
    'zomcat',
])

ENTITY_TYPES = {
    'appdomain': [
        'id',
        'code',
        'locale',
        'name',
        'url',
    ],
    'city': [
        'id',
        'city',
        'accentcity',
        'country',
        'region',
        'population',
        'latitude',
        'longitude',
    ],
    'database': ['id', 'name', 'environment', 'role', 'slave_type'],
    'database_cluster_instance': [
        'id',
        'host',
        'data_center_code',
        'cluster',
        'role',
        'environment',
        'service_name',
        'port',
        'version',
        'pci',
    ],
    'dnsdomain': ['name'],
    'GLOBAL': [],
    'host': [
        'id',
        'host',
        'host_role_id',
        'external_ip',
        'internal_ip',
        'physical_machine_model',
        'virt_type',
        'data_center_code',
    ],
    'mysqldb': ['id', 'name', 'environment', 'role'],
    'oracledb': [
        'id',
        'name',
        'environment',
        'role',
        'host',
        'port',
        'sid',
    ],
    'mssqldb': [
        'id',
        'name',
        'environment',
        'role',
        'host',
        'port',
        'database',
        ],
    'php': [
        'id',
        'environment',
        'project',
        'team',
        'url',
        'path',
        'host',
        'data_center_code',
        'instance',
        'project_type',
    ],
    'project': [
        'id',
        'name',
        'team',
        'project_type',
        'instance_type',
        'deployable',
    ],
    'zomcat': [
        'id',
        'environment',
        'project',
        'team',
        'url',
        'path',
        'host',
        'data_center_code',
        'instance',
        'project_type',
    ],
    'zompy': [
        'id',
        'environment',
        'project',
        'team',
        'url',
        'path',
        'host',
        'data_center_code',
        'instance',
        'project_type',
    ],
}


### CHECKING ###

def main():
    arguments = parse_command_line_arguments()
    set_up_logging(arguments.loglevel)
    result = check_files(arguments.files)
    sys.exit(result)


def check_files(file_names):
    LOGGER.debug('Validating %d file%s...', len(file_names), 's' * (len(file_names) != 1))
    worst_result = RESULT_OK
    for name in file_names:
        result = check_one_file(name)
        worst_result = max(result, worst_result)

    if worst_result == RESULT_OK:
        LOGGER.info('All files passed validation. Yay!')
    elif worst_result == RESULT_VALIDATION_ISSUES:
        LOGGER.info('There were minor validation issues.')
    else:
        LOGGER.warning('There were validation errors. :(')

    return worst_result


def check_one_file(file_name):
    LOGGER.debug('Validating "%s".', file_name)
    worst_result = RESULT_OK

    if not file_name.endswith('.yaml'):
        LOGGER.warning('The file "%s" does not have the extension ".yaml".', file_name)
        worst_result = RESULT_VALIDATION_FAILED

    try:
        with open(file_name) as check_file:
            contents = check_file.read()
    except EnvironmentError, e:
        LOGGER.error('The file "%s" cannot be read. The error was %s: "%s".', file_name, e.__class__.__name__, e)
        worst_result = RESULT_ERRORS
    else:
        result = check_contents(file_name, contents)
        worst_result = max(result, worst_result)

    if worst_result == RESULT_OK:
        LOGGER.info('The file "%s" passed validation.', file_name)

    return worst_result


def check_contents(file_name, contents):
    try:
        check = yaml.safe_load(contents)
    except Exception, e:
        message = str(e).replace('\n', '\n    ')
        LOGGER.warning('The file "%s" does not contain valid YAML. The error message was:\n    %s', file_name, message)
        return RESULT_VALIDATION_FAILED

    if not isinstance(check, dict):
        LOGGER.warning('The top-level YAML object in the file "%s" isn\'t a mapping.', file_name)
        return RESULT_VALIDATION_FAILED

    worst_result = RESULT_OK

    for field in MANDATORY_FIELDS:
        value = check.get(field, NOT_SET)
        if value is NOT_SET:
            LOGGER.warning('The file %s does not contain the mandatory field "%s".', file_name, field)
            worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
        else:
            result = globals()['check_' + field](file_name, value)
            worst_result = max(result, worst_result)

    for field in OPTIONAL_FIELDS:
        result = globals()['check_' + field](file_name, check.get(field, NOT_SET))
        worst_result = max(result, worst_result)

    extra_fields = ', '.join(sorted(str(k) for k in set(check.iterkeys()) - MANDATORY_FIELDS - OPTIONAL_FIELDS))
    if extra_fields:
        LOGGER.info('The file "%s" specifies the following fields which will be ignored: %s.', file_name, extra_fields)
        worst_result = max(RESULT_VALIDATION_ISSUES, worst_result)

    return worst_result


def check_status(file_name, value):
    if value in STATUSES:
        return RESULT_OK
    else:
        statuses = ', '.join(s for s in STATUSES)
        LOGGER.warning('The file "%s" has an invalid status. The status must be in {%s}.', file_name, value, statuses)
        return RESULT_VALIDATION_FAILED


def check_name(file_name, value):
    if value is None:
        LOGGER.warning('The file "%s" does not specify a name.' % file_name)
        return RESULT_VALIDATION_FAILED
    elif not isinstance(value, str):
        LOGGER.warning('The file "%s" has an invalid name. Names must be strings.', file_name)
        return RESULT_VALIDATION_FAILED

    worst_result = RESULT_OK

    if value.startswith(' ') or value.endswith(' '):
        LOGGER.warning('The file "%s" has an invalid name. Names must not contain leading or trailing spaces.',
                       file_name)
        worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
    if len(value) > MAX_NAME_LENGTH:
        LOGGER.warning('The file "%s" has an invalid name. Names must not exceed %d characters.', file_name,
                       MAX_NAME_LENGTH)
        worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
    if len(value) == 0:
        LOGGER.warning('The file "%s" has an invalid name. Names must not be empty strings.', file_name)
        worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

    return worst_result


def check_interval(file_name, value):
    if value is None:
        LOGGER.warning('The file "%s" does not specify an interval.', file_name)
        return RESULT_VALIDATION_FAILED
    elif not isinstance(value, (int, long)):
        LOGGER.warning('The file "%s" has an invalid interval. Intervals must be integers.', file_name)
        return RESULT_VALIDATION_FAILED
    elif value <= 0:
        LOGGER.warning('The file "%s" has an invalid interval. Intervals must be positive.', file_name)
        return RESULT_VALIDATION_FAILED
    elif value > MAX_INTERVAL:
        LOGGER.warning('The file "%s" has an invalid interval. Intervals must not exceed %d.', file_name, MAX_INTERVAL)
        return RESULT_VALIDATION_FAILED
    else:
        return RESULT_OK


def check_entities(file_name, value):
    if value is None or isinstance(value, list) and len(value) == 0:
        LOGGER.warning('The file "%s" does not specify any entities.', file_name)
        return RESULT_VALIDATION_FAILED
    elif not isinstance(value, list) or not all(isinstance(e, dict) for e in value):

        LOGGER.warning('The file "%s" has a entities. Entities must be a list of mappings.', file_name)
        return RESULT_VALIDATION_FAILED

    worst_result = RESULT_OK

    for d in value:
        if 'type' not in d:
            LOGGER.warning('The file "%s" has an entity without a type.', file_name)
            worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
        elif d['type'] not in ENTITY_TYPES:
            LOGGER.warning('The file "%s" has an entity with the unknown type %s.', file_name, d['type'])
            worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

        for k, v in d.iteritems():
            if not isinstance(k, str):
                LOGGER.warning('The file "%s" has an entity with the key %s, which is not a string.', file_name, k)
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
            if not isinstance(v, str):
                LOGGER.warning('The file "%s" has an entity with the key %s whose value is not a string.', file_name, k)
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)
            if k != 'type' and 'type' in d and d['type'] in ENTITY_TYPES and k not in ENTITY_TYPES[d['type']]:
                LOGGER.warning('The file "%s" has an entity with the unknown key %s.', file_name, k)
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

    return worst_result


def check_command(file_name, value):
    if value is None:
        LOGGER.warning('The file "%s" does not specify a command.', file_name)
        return RESULT_VALIDATION_FAILED
    elif not isinstance(value, str):
        LOGGER.warning('The file "%s" has an invalid command. Commands must be strings.', file_name)
        return RESULT_VALIDATION_FAILED
    else:
        try:
            tree = ast.parse(value)
        except SyntaxError, e:
            LOGGER.warning('''The file "%s" has a command that isn\'t valid Python. The parser error was "%s":
    %s
    %s^''',
                           file_name, e.msg, e.text.rstrip('\n'), ' ' * e.offset)
            return RESULT_VALIDATION_FAILED
        else:
            nodes = list(ast.walk(tree))
            worst_result = RESULT_OK
            statements = set(n.__class__.__name__ for n in nodes if isinstance(n, ast.stmt) and not isinstance(n,
                             ast.Expr))
            if statements:
                LOGGER.warning('The file "%s" has a command that includes statements of the following types: %s.',
                               file_name, ', '.join(sorted(statements)))
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

            gno = GlobalNameOutfigurer()
            gno.visit(tree)
            bad_globals = ', '.join(sorted(gno.global_names - ALLOWED_GLOBALS))
            if bad_globals:
                LOGGER.warning('The file "%s" has a command that uses the following unavailable globals: %s.',
                               file_name, bad_globals)
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

            if '__' in value:
                LOGGER.warning('The file "%s" has a command that includes double underscores. That\'s not allowed. No, not even in string literals.'
                               , file_name)
                worst_result = max(RESULT_VALIDATION_FAILED, worst_result)

            return worst_result


def check_technical_details(file_name, value):
    return check_optional_str(value, lambda *args: \
                              LOGGER.warning('The file "%s" has invalid technical details. Technical details must be a string.'
                              , file_name))


def check_potential_analysis(file_name, value):
    return check_optional_str(value, lambda *args: \
                              LOGGER.warning('The file "%s" has invalid potential analysis. Potential analysis must be a string.'
                              , file_name))


def check_potential_impact(file_name, value):
    return check_optional_str(value, lambda *args: \
                              LOGGER.warning('The file "%s" has invalid potential impact. Potential impact must be a string.'
                              , file_name))


def check_potential_solution(file_name, value):
    return check_optional_str(value, lambda *args: \
                              LOGGER.warning('The file "%s" has invalid potential solution. Potential solution must be a string.'
                              , file_name))


def check_optional_str(value, log_function):
    if value is not NOT_SET and not isinstance(value, str):
        log_function()
        return RESULT_VALIDATION_FAILED
    else:
        return RESULT_OK


class GlobalNameOutfigurer(ast.NodeVisitor):

    def __init__(self):
        self.local_names = set()
        self.global_names = set()
        self.parameter_stack = []

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.AugStore)):
            self.local_names.add(node.id)
        elif isinstance(node.ctx, ast.Param) and node.id not in self.local_names:
            self.local_names.add(node.id)
            self.parameter_stack[-1].add(node.id)
        elif node.id not in self.local_names:
            self.global_names.add(node.id)
        self.generic_visit(node)

    def visit_arguments(self, node):
        if node.vararg:
            self.local_names.add(node.vararg)
        if node.kwarg:
            self.local_names.add(node.kwarg)
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.visit_Comp(node)

    def visit_DictComp(self, node):
        for n in node.generators:
            self.visit(n)
        self.visit(node.key)
        self.visit(node.value)

    def visit_SetComp(self, node):
        self.visit_Comp(node)

    def visit_GeneratorExp(self, node):
        self.visit_Comp(node)

    def visit_Comp(self, node):
        for n in node.generators:
            self.visit(n)
        self.visit(node.elt)

    def visit_Lambda(self, node):
        self.parameter_stack.append(set())
        self.generic_visit(node)
        for n in self.parameter_stack.pop():
            self.local_names.remove(n)


def check_description(file_name, value):
    if value is None:
        LOGGER.warning('The file "%s" does not specify a description.', file_name)
        return RESULT_VALIDATION_FAILED
    elif not isinstance(value, str):
        LOGGER.warning('The file "%s" has an invalid description. Descriptions must be strings.', file_name)
        return RESULT_VALIDATION_FAILED
    else:
        return RESULT_OK


### COMMAND LINE ARGUMENTS ###

def parse_command_line_arguments():
    return create_command_line_argument_parser().parse_args()


def create_command_line_argument_parser():
    parser = argparse.ArgumentParser(description='Validate ZMON 2 check definition files.')
    parser.add_argument('files', metavar='FILE', nargs='+', help='A file that is to be checked.')
    parser.add_argument('-q', '--quiet', dest='loglevel', action='store_const', const=logging.WARNING,
                        default=logging.INFO, help='Only print problems, not informational messages.')
    parser.add_argument('-v', '--verbose', dest='loglevel', action='store_const', const=logging.DEBUG,
                        default=logging.INFO, help='Print debug output.')
    return parser


### LOGGING ###

LOG_FORMAT = '%(levelname)s: %(message)s'


def set_up_logging(level):
    global LOGGER
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(level)
    LOGGER = logger


### ANOTHER IMPORT ###

try:
    import yaml
except ImportError:
    if sys.platform.startswith('linux'):
        solution = 'Try `sudo apt-get install python-yaml`.'
    elif sys.platform == 'darwin':
        solution = 'Try `sudo easy_install pyyaml`.'
    else:
        solution = 'Also, you\'re using some kind of weird-ass OS. Try `easy_install pyyaml`, but no guarantees.'
    print 'ERROR: The yaml module for Python isn\'t available.', solution
    sys.exit(4)

### MAIN ENTRYPOINT ###

if __name__ == '__main__':
    main()

