__author__ = 'steven'

import sys
import os
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import config


class Mail:
    def __init__(self, subject, to,
                 _from="looney.tunes@epitech.eu", smtp="smtp.epita.fr",
                 port=25, login=None,
                 password=None, ssl=False):
        self._subject = subject
        self._to = to
        self._content = ""
        self._from = _from
        self._login = login
        self._password = password
        self._smtp = smtp
        self._port = port
        self._ssl = ssl
        self._file = False

    def content(self, content):
        self._content = content

    def file(self, content):
        self._file = content

    def send(self):
        #Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
        msg = MIMEMultipart("mixed")
        msg['Subject'] = self._subject
        msg['From'] = self._from
        msg['To'] = self._to

        text = MIMEText(self._content, "plain", "utf-8")
        msg.attach(text)
        if self._file:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(self._file,"rb").read() )
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(self._file))
            msg.attach(part)
        i = 1
        while i < 3:
            try:
                s = smtplib.SMTP(self._smtp, self._port)
                s.ehlo()
                s.starttls()
                s.ehlo()
                if self._login and self._password:
                    s.login(self._login, self._password)
                s.sendmail(self._from, [self._to], msg.as_string())
                s.quit()
                return True
            except Exception as e:
                i += 1
                logging.warning("%s: error... retry %s, reason: %s" % (self._to, str(i), str(e)))
                time.sleep(1)
        return False



class MailMixin(object):
    def __init__(self):
        pass

    def _send_mail(self, to, subject, content, attached=None):
        try:
            m = Mail(subject, to,
                 _from=config.SMTP_FROM, smtp=config.SMTP_SERVER,
                 port=config.SMTP_PORT, login=config.SMTP_LOGIN,
                 password=config.SMTP_PASSWORD, ssl=config.SMTP_SSL)
            m.content(content)
            if attached:
                m.file(attached)
        except ImportError as e:
            logging.warning("send_mail: import_error %s" % (str(e)))
            return None
        return m.send()

    def send_mail(self, to, subject, content, attached=None):
        if isinstance(to, list):
            for t in to:
                self._send_mail(t, subject, content, attached)
        else:
            return self._send_mail(to, subject, content, attached)