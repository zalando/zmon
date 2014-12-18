#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jinja2
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from notification import BaseNotification

import logging
logger = logging.getLogger(__name__)

thisdir = os.path.join(os.path.dirname(__file__))
template_dir = os.path.join(thisdir, '../templates/mail')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


class Mail(BaseNotification):

    @classmethod
    def send(cls, alert, *args, **kwargs):
        sender = cls._config.get('notifications.mail.sender')
        subject = cls._get_subject(alert, custom_message=kwargs.get('subject'))
        html = kwargs.get('html', False)
        cc = kwargs.get('cc', [])
        hide_recipients = kwargs.get('hide_recipients', True)
        repeat = kwargs.get('repeat', 0)
        expanded_alert_name = cls._get_expanded_alert_name(alert)

        try:
            tmpl = jinja_env.get_template('alert.txt')
            body_plain = tmpl.render(expanded_alert_name=expanded_alert_name, **alert)
        except Exception:
            logger.exception('Error parsing email template for alert %s with id %s', alert['name'], alert['id'])
        else:
            if html:
                msg = MIMEMultipart('alternative')
                tmpl = jinja_env.get_template('alert.html')
                body_html = tmpl.render(expanded_alert_name=expanded_alert_name, **alert)
                part1 = MIMEText(body_plain.encode('utf-8'), 'plain', 'utf-8')
                part2 = MIMEText(body_html.encode('utf-8'), 'html', 'utf-8')
                msg.attach(part1)
                msg.attach(part2)
            else:
                msg = MIMEText(body_plain.encode('utf-8'), 'plain', 'utf-8')

            msg['Subject'] = subject
            msg['From'] = 'ZMON 2 <{}>'.format(sender)

            args = BaseNotification.resolve_group(args)

            if hide_recipients:
                msg['To'] = 'Undisclosed Recipients <{}>'.format(sender)
                msg['Bcc'] = ', '.join(args)
            else:
                msg['To'] = ', '.join(args)
            msg['Cc'] = ', '.join(cc)

            if cls._config.get('notifications.mail.on', True):
                try:
                    s = smtplib.SMTP(cls._config.get('notifications.mail.host', 'localhost'),
                                     cls._config.get('notifications.mail.port', 25))
                except Exception:
                    logger.exception('Error connecting to SMTP server for alert %s with id %s', alert['name'],
                                     alert['id'])
                else:
                    try:
                        s.sendmail(sender, list(args) + cc, msg.as_string())
                    except Exception:
                        logger.exception('Error sending email for alert %s with id %s', alert['name'], alert['id'])
                    finally:
                        s.quit()
        finally:
            return repeat


if __name__ == '__main__':
    import sys
    Mail.send({'entity': {'id': 'test'}, 'value': 5}, *sys.argv[1:])
