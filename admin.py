__author__ = 'steven'


from flask import request, Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import config

import os
import csv
import logging
import bcrypt
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_DB_URI
app.secret_key = os.urandom(40)
try:
    if config.DEBUG:
        app.debug = True
except ImportError:
    pass

db = SQLAlchemy(app)

auth = HTTPBasicAuth()

from flask_admin import Admin
from flask_admin import expose
from flask_admin import AdminIndexView
from flask import redirect
from flask import url_for
from flask_admin.contrib.sqla import ModelView as MView


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
    if username not in config.USER_WHITELIST:
        return None
    if Auth.checkInPasswd(username, password):
        return True
    logging.warning("authenticate: %s, password mismatch" % username)
    return None


def is_authenticated():
    if auth.username() and auth.username() in config.USER_WHITELIST:
        return True
    return False

class ModelView(MView):
    def is_accessible(self):
            #if not is_authenticated():
            #    logging.error("is_accessible: Not authenticated")
            #    return redirect("/")
            return is_authenticated()
    #def is_accessible(self):
    #    return is_authenticated()
#
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            return redirect("/admin/")


class AdminIndexView(AdminIndexView):
    @auth.login_required
    @expose('/')
    def index(self):
        #if not is_authenticated():
        #    return authenticate()
        return super(AdminIndexView, self).index()


class UserModelView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = ('login', 'firstname', 'lastname')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(UserModelView, self).__init__(User, session, **kwargs)



class ProjectModelView(ModelView):
    # Disable model creation
    #can_create = False

    # Override displayed fields
    column_list = ('token', 'scolaryear', 'deadline', 'module_title', 'module_code',
                   'instance_code', 'location', 'title', 'promo', 'template', 'last_update', 'last_action')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ProjectModelView, self).__init__(Project, session, **kwargs)


admin = Admin(app, name="Ramassage2", index_view=AdminIndexView())

from models import Project, Task, User, Template
admin.add_view(UserModelView(db.session))
admin.add_view(ProjectModelView(db.session))
admin.add_view(ModelView(Task, db.session))
admin.add_view(ModelView(Template, db.session))


if __name__ == "__main__":
    app.run()
