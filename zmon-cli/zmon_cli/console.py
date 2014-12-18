import click
import datetime
import time


STYLES = {
    'REGISTERED': {'fg': 'green'},
    'UNKNOWN': {'fg': 'red'},
    'RUNNING': {'fg': 'green'},
    'START': {'fg': 'white', 'bold': True},
    'STARTING': {'fg': 'yellow'},
    'KILL': {'fg': 'white', 'bold': True},
    'KILLING': {'fg': 'red'},
}

MAX_COLUMN_WIDTH = {
    'node_name': 32,
    'command': 16
}


def action(msg, **kwargs):
    click.secho(msg.format(**kwargs), nl=False, bold=True)


def ok(**kwargs):
    click.secho(' OK', fg='green', bold=True, **kwargs)


def error(msg, **kwargs):
    click.secho(' {}'.format(msg), fg='red', bold=True, **kwargs)

def highlight(msg, **kwargs):
    click.secho(' {}'.format(msg), fg='cyan',nl=False, bold=True, **kwargs)

def format_time(ts):
    if ts == 0:
        return ''
    now = datetime.datetime.now()
    try:
        dt = datetime.datetime.fromtimestamp(ts)
    except:
        return ts
    diff = now - dt
    s = diff.total_seconds()
    if s > 3600:
        t = '{:.0f}h'.format(s / 3600)
    elif s > 60:
        t = '{:.0f}m'.format(s / 60)
    else:
        t = '{:.0f}s'.format(s)
    return '{} ago'.format(t)


def format(col, val):
    if val is None:
        val = ''
    elif col.endswith('_time'):
        val = format_time(val)
    elif isinstance(val, bool):
        val = 'yes' if val else 'no'
    else:
        val = str(val)
    return val


def print_table(cols, rows):
    colwidths = {}

    for col in cols:
        colwidths[col] = len(TITLES.get(col, col))

    for row in rows:
        for col in cols:
            val = row.get(col)
            colwidths[col] = min(max(colwidths[col], len(format(col, val))), MAX_COLUMN_WIDTH.get(col, 1000))

    for col in cols:
        click.secho(('{:' + str(colwidths[col]) + '}').format(TITLES.get(col, col.title().replace('_', ' '))),
                    nl=False, fg='black', bg='white')
        click.secho(' ', nl=False, fg='black', bg='white')
    click.echo('')

    for row in rows:
        for col in cols:
            val = row.get(col)
            align = ''
            style = STYLES.get(val, {})
            if val is not None and col.endswith('_time'):
                align = '>'
                diff = time.time() - val
                if diff < 900:
                    style = {'fg': 'green', 'bold': True}
                elif diff < 3600:
                    style = {'fg': 'green'}
            elif isinstance(val, int):
                align = '>'
            val = format(col, val)

            if len(val) > MAX_COLUMN_WIDTH.get(col, 1000):
                val = val[:MAX_COLUMN_WIDTH.get(col, 1000) - 2] + '..'
            click.secho(('{:' + align + str(colwidths[col]) + '}').format(val), nl=False, **style)
            click.echo(' ', nl=False)
        click.echo('')


def print_permissions(permissions):
    cols = 'path comment'.split()
    rows = []
    for row in permissions:
        rows.append({'path': row['path'], 'comment': (row['comment'] or '') + row['path_comments']})

    print_table(cols, rows)