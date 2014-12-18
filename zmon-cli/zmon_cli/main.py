#!/usr/bin/env python2
import json
import zmon_cli

from zmon_cli.console import action, ok, error, highlight

import click
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
import yaml
import time

from redis import StrictRedis

DEFAULT_CONFIG_FILE = '~/.zmon-cli.yaml'

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('ZMON CLI {}'.format(zmon_cli.__version__))
    ctx.exit()


def configure_logging(loglevel):
    # configure file logger to not clutter stdout with log lines
    logging.basicConfig(level=loglevel, filename='/tmp/zmon-cli.log',
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option('--config-file', help='Use alternative config file', default=DEFAULT_CONFIG_FILE, metavar='PATH')
@click.option('-v', '--verbose', help='Verbose logging', is_flag=True)
@click.option('-V', '--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True)
@click.pass_context
def cli(ctx, config_file, verbose):
    """
    zmon command line interface
    """
    configure_logging(logging.DEBUG if verbose else logging.INFO)
    fn = os.path.expanduser(config_file)
    data = {}
    if os.path.exists(fn):
        with open(fn) as fd:
            data = yaml.safe_load(fd)
    ctx.obj = data


def check_redis_host(host, port=6379):
    action("Check Redis on {}".format(host))
    action("...")
    try:
        r = StrictRedis(host, port)
        workers = r.smembers("zmon:metrics")
        ok()
        return r, workers
    except Exception as e:
        error(e)


def check_queues(redis):
    queues = ['zmon:queue:default', 'zmon:queue:snmp', 'zmon:queue:internal', 'zmon:queue:secure']

    for q in queues:
        action('Checking queue length ... {} ...'.format(q))
        l = redis.llen(q)
        action("...")
        highlight("{}".format(l))
        action(" ...")
        if l < 2000:
            ok()
            continue
        error("to many tasks")


def check_schedulers(r, schedulers):
    for s in schedulers:
        action('Check scheduler {} .....'.format(s[2:]))
        try:
            ts = r.get("zmon:metrics:{}:ts".format(s))
            if ts is None:
                error("No scheduling loop registered ( running/stuck? )")
                continue

            delta = int(time.time() - float(ts))
            action("... last loop")
            highlight("{}".format(delta))
            action("s ago ...")
            if delta > 300:
                error("Last loop more than 300s ago (stuck? restart?)".format(delta))
                continue

            if delta > 180:
                error("Last loop more than 180s ago (stuck? check logs/watch)".format(delta))
                continue

            action("...")
            ok()
        except Exception as e:
            error(e)


def check_workers(r, workers):
    for w in workers:
        action('Check worker {} ...'.format(w))
        try:
            ts = r.get("zmon:metrics:{}:ts".format(w))
            delta = time.time() - float(ts)
            delta = max(int(delta), 0)

            action("... last exec")
            highlight("{}".format(delta))
            action("s ago ...")
            if delta < 30:
                ok()
                continue

            error("no task execute recently")

        except Exception as e:
            error(e)


def get_config_data():
    fn = os.path.expanduser(DEFAULT_CONFIG_FILE)
    data = {}
    if os.path.exists(fn):
        with open(fn) as fd:
            data = yaml.safe_load(fd)

            if "user" not in data or "password" not in data:
                raise Exception("Config file not found/properly configured: ~/.zmon-cli.yaml with user: and password:")

        return data


def get(url):
    data = get_config_data()
    try:
        return requests.get(data['url']+url, auth=HTTPBasicAuth(data['user'], data['password']))
    except Exception as e:
        logging.error(e)

    return None


def put(url):
    data = get_config_data()
    try:
        return requests.put(data['url']+url, None, auth=HTTPBasicAuth(data['user'], data['password']))
    except Exception as e:
        logging.error(e)

    return None


def delete(url):
    data = get_config_data()
    try:
        return requests.delete(data['url']+url, auth=HTTPBasicAuth(data['user'], data['password']))
    except Exception as e:
        logging.error(e)

    return None


@cli.group()
@click.pass_context
def members(ctx):
    """manage group membership"""
    pass


@cli.group('check-definitions')
@click.pass_context
def check_definitions(ctx):
    """manage check definitions"""
    pass


@check_definitions.command()
@click.argument('yaml_file', type=click.File('rb'))
def update(yaml_file):
    """update a single check definition"""
    data = get_config_data()
    post = yaml.safe_load(yaml_file)
    post['last_modified_by'] = data['user']
    if 'status' not in post:
        post['status'] = 'ACTIVE'
    action('Updating check definition..')
    r = requests.post(data['url'] + '/check-definitions', json.dumps(post),
                      auth=HTTPBasicAuth(data['user'], data['password']), headers={'Content-Type': 'application/json'})
    print(r.text)


@cli.group(invoke_without_command=True)
@click.pass_context
def groups(ctx):
    """manage contact groups"""
    if not ctx.invoked_subcommand:
        r = get("/groups/")
        for t in r.json():
            print("Name: {} Id: {}".format(t["name"], t["id"]))
            print("\tMembers:")
            for m in t["members"]:
                m = get("/groups/member/{}/".format(m)).json()
                print("\t\t{} {} {}".format(m["name"], m["email"], m["phones"]))
            print("\tActive:")
            for m in t["active"]:
                m = get("/groups/member/{}/".format(m)).json()
                print("\t\t{} {} {}".format(m["name"], m["email"], m["phones"]))


@groups.command("switch")
@click.argument("group_name")
@click.argument("user_name")
@click.pass_context
def switch_active(ctx, group_name, user_name):
    action("Switching active user ....")
    r = delete("/groups/{}/active/".format(group_name))
    r = put("/groups/{}/active/{}/".format(group_name, user_name))
    if r.text == '1':
        ok()
    else:
        error("failed to switch")


@members.command("add")
@click.argument("group_name")
@click.argument("user_name")
@click.pass_context
def group_add(ctx, group_name, user_name):
    action("Adding user ....")
    r = put("/groups/{}/member/{}/".format(group_name, user_name))
    if r.text == '1':
        ok()
    else:
        error("failed to insert")


@members.command("remove")
@click.argument("group_name")
@click.argument("user_name")
@click.pass_context
def group_remove(ctx, group_name, user_name):
    action("Removing user ....")
    r = delete("/groups/{}/member/{}/".format(group_name, user_name))
    if r.text == '1':
        ok()
    else:
        error("failed to remove")


@members.command("add-phone")
@click.argument("member_email")
@click.argument("phone_nr")
@click.pass_context
def add_phone(ctx, member_email, phone_nr):
    action("Adding phone ....")
    r = put("/groups/{}/phone/{}/".format(member_email, phone_nr))
    if r.text == '1':
        ok()
    else:
        error("failed to set phone")


@members.command("remove-phone")
@click.argument("member_email")
@click.argument("phone_nr")
@click.pass_context
def remove_phone(ctx, member_email, phone_nr):
    action("Removing phone number ....")
    r = delete("/groups/{}/phone/{}/".format(member_email, phone_nr))
    if r.text == '1':
        ok()
    else:
        error("failed to remove phone")


@members.command("change-name")
@click.argument("member_email")
@click.argument("member_name")
@click.pass_context
def set_name(ctx, member_email, member_name):
    action("Chaning user name ....")
    r = put("/groups/{}/name/{}/".format(member_email, member_name))
    ok()


@cli.command()
@click.pass_obj
def status(ctx):
    """check system status"""
    redis, workers = check_redis_host('monitor03', 6379)

    print("")

    workers = sorted(workers)

    action("Looking for <30s interval scheduler ...")
    found_p3423 = False
    scheduler = filter(lambda x: x[:7]=='s-p3423', workers)
    if len(scheduler)==0:
        error("not found! check p3423")
    else:
        action("... running {}".format(scheduler[0][2:]))
        ok()


    action("Looking for >30s interval scheduler ...")
    found_p3422 = False
    scheduler = filter(lambda x: x[:7]=='s-p3422', workers)
    if len(scheduler)==0:
        error("not found! check p3422")
    else:
        action("... running {}".format(scheduler[0][2:]))
        ok()

    print("")

    ws = []
    ss = []

    for w in workers:
        if w[:2] == b"s-":
            ss.append(w)
        else:
            ws.append(w)

    check_schedulers(redis, ss)
    print("")

    check_queues(redis)
    print("")

    check_workers(redis, ws)


@cli.command()
@click.pass_context
def help(ctx):
    pass


def main():
    try:
        cli()
    except requests.HTTPError as e:
        click.secho('', bold=True, fg='red')
