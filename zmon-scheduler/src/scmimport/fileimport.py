#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from suds.client import Client as SoapClient

import logging
import yaml

MANDATORY_FIELDS = set([
    'name',
    'description',
    'entities',
    'interval',
    'command',
    'status',
])

logger = logging.getLogger('zmon-import')


class MalformedCheckDefinitionError(Exception):

    def __init__(self, reason):
        self.reason = reason
        super(MalformedCheckDefinitionError, self).__init__()


def get_soap_client(endpoint):
    soap_client = SoapClient(endpoint)
    return soap_client


def import_from_stream(soap_client, check_data, source_url, team, user):
    logger.info('Importing %s for %s..', source_url, team)

    for key in MANDATORY_FIELDS:
        if key not in check_data:
            raise MalformedCheckDefinitionError('Missing required property: {}'.format(key))

    if not all('type' in e for e in check_data['entities']):
        raise MalformedCheckDefinitionError('Missing type in entity definition: {}'.format(check_data['entities']))

    check_definition = soap_client.factory.create('checkDefinitionImport')

    check_definition.name = check_data['name']
    check_definition.description = check_data['description']
    check_definition.technicalDetails = check_data.get('technical_details')
    check_definition.potentialAnalysis = check_data.get('potential_analysis')
    check_definition.potentialImpact = check_data.get('potential_impact')
    check_definition.potentialSolution = check_data.get('potential_solution')
    check_definition.owningTeam = team
    check_definition.interval = check_data['interval']
    check_definition.command = check_data['command']
    check_definition.status = check_data['status']
    check_definition.sourceUrl = source_url
    check_definition.lastModifiedBy = user

    entities = soap_client.factory.create('entities')
    entities.entity = []

    for entry in check_data['entities']:
        entity = soap_client.factory.create('entity')

        entity.attributes = {'attribute': []}
        for key, value in entry.iteritems():
            attribute = soap_client.factory.create('entityAttribute')
            attribute.key = key
            attribute.value = (str(value).lower() if type(value) == bool else value)  # PF-3395
            entity.attributes['attribute'].append(attribute)

        entities.entity.append(entity)

    check_definition.entities = entities

    soap_client.service.createOrUpdateCheckDefinition(check_definition, timeout=10)


if __name__ == '__main__':
    parser = ArgumentParser(description='ZMON check definition importer')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity level')
    group.add_argument('-q', '--quiet', action='store_true', help='Decrease verbosity level')

    parser.add_argument('target_file', help='File to import')
    parser.add_argument('-t', '--team', required=True, help='Owning team')
    parser.add_argument('-u', '--user', required=True, help='User that modified the file')
    parser.add_argument('-e', '--endpoint', required=True, help='SOAP WSDL URL')

    args = parser.parse_args()
    logging.basicConfig()
    loglevel = logging.INFO

    if args.quiet:
        loglevel = logging.WARN
    if args.verbose:
        loglevel = logging.DEBUG

    logger.setLevel(loglevel)

    soap_client = get_soap_client(args.endpoint)
    with open(args.target_file, 'r') as stream:
        check_data = yaml.safe_load(stream)
        import_from_stream(soap_client, check_data, args.target_file, args.team, args.user)
