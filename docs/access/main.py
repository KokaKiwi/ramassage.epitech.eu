from flask import Flask, send_from_directory, request
from flask_httpauth import HTTPBasicAuth
import os
import datetime
import csv
import bcrypt
import config
import logging

app = Flask(__name__)
auth = HTTPBasicAuth()
app.debug = True if config.DEBUG else False


class Mapping(object):
    def _get_users(self):
        try:
            users = {}
            with open(config.PASSWORD_FILE, 'r') as f:
                reader = csv.reader(f, delimiter=':', quoting=csv.QUOTE_NONE)
                #0: login
                #1: password
                #7: firstname lastname

                for row in reader:
                    if len(row[7].split(" ")) != 2:
                        continue
                    firstname, lastname = row[7].split(" ")
                    users[row[0]] = "%s.%s@epitech.eu" % (firstname, lastname)
                return users
        except Exception as e:
            logging.error(str(e))
        return {}

    def __getattr__(self, name):
        if name == 'users':
            users = self.users = self._get_users()
            return users
        return super(Mapping, self).__getattr__(name)

mapping = Mapping()


class Auth(object):
    @staticmethod
    def checkHash(encrypted, plain):
        if bcrypt.hashpw(plain, encrypted) == encrypted:
            return True
        return False

    @staticmethod
    def checkInPasswd(login, password):
        with open(config.PASSWORD_FILE, 'r') as f:
            reader = csv.reader(f, delimiter=':', quoting=csv.QUOTE_NONE)
            for row in reader:
                if row[0] == login:
                    return Auth.checkHash(row[1].encode('utf-8'), password.encode('utf-8'))
        return False

@auth.verify_password
def authenticate(username=None, password=None):
    logging.info("authenticate: %s" % username)
    if not os.path.exists(os.path.join(config.BASE_DIR, mapping.users[username] if username in mapping.users else username)):
        logging.warning("authenticate: %s, path not found" % username)
        return None
    if Auth.checkInPasswd(username, password):
        return True
    logging.warning("authenticate: %s, password mismatch" % username)
    return None

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

@app.route('/<path:path>')
@app.route('/')
@auth.login_required
def index(path=""):
    alt=False
    username = mapping.users[auth.username()] if auth.username() in mapping.users else auth.username()
    if 'alt' in request.args:
        username = auth.username()
        alt = True
    rpath = "~%s/%s" % (username, path)
    output = "<html><head><title>Index of /%s</title></head>" \
             "<body bgcolor='white'>" \
             "<h1>Index of /%s</h1><hr><pre>" % (rpath, rpath)
    d = os.path.join(config.BASE_DIR, username)
    d = os.path.join(d, path)
    d = os.path.realpath(d)
    if len(d) < len(os.path.join(config.BASE_DIR, username)):
        return "Not allowed", 403
    if os.path.isfile(d):
        logging.warning("send_from_directory: %s, %s" % (os.path.join(config.BASE_DIR, username), path))
        return send_from_directory(os.path.join(config.BASE_DIR, username), path)

    output += "{:<60}{:^20}{:>10}\r\n".format("..", "-", "-").replace("..", "<a href='/%s%s'>..</a>" %
                                                                      ("/".join(path.split("/")[:-1]), "?alt" if alt else ""))
    for f in sorted(os.listdir(d)):
        stat = os.lstat(os.path.join(d, f))
        date = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        output += "{:<60}{:^20}{:>10}\r\n".format(f, date, sizeof_fmt(stat.st_size)).replace(f,
                                                                                             "<a href='/%s%s'>%s</a>" %
                                                                                             (os.path.join(path, f.replace(" ", "%20")), "?alt" if alt else "", f))
    output += "</pre><hr>" \
              "</body></html>"
    return output

if __name__ == '__main__':
    app.run()
