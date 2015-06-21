__author__ = 'steven'


from flask import request, Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
import config

import os
import csv
import logging
import bcrypt
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__, template_folder='admin_templates')
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
from flask_admin import BaseView
from flask_admin import expose
from flask_admin import AdminIndexView
from flask import redirect, render_template
from flask import url_for
from flask_admin.contrib.sqla import ModelView as MView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual, FilterInList, FilterLike
from flask_admin.form import rules

from datetime import datetime

from models import Project, Task, User, Template, Project_Student

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
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'

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
            return redirect("/admin_templates/")


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


    #column_filters = [
    #    FilterEqual(User.firstname, 'First name')
    #    #FilterInList(Template.school, 'school'),
    #    #FilterLike(Template.codemodule, 'codemodule')
    #]

    column_searchable_list = ('login', 'lastname')


    def is_accessible(self):
            #if not is_authenticated():
            #    logging.error("is_accessible: Not authenticated")
            #    return redirect("/")
            return is_authenticated()

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(UserModelView, self).__init__(User, session, **kwargs)



class ProjectModelView(ModelView):
    # Disable model creation
    can_create = False
    can_edit = False
    can_delete = False
    def is_accessible(self):
            #if not is_authenticated():
            #    logging.error("is_accessible: Not authenticated")
            #    return redirect("/")
            return is_authenticated()
    # Override displayed fields
    column_list = ('token', 'scolaryear', 'deadline', 'module_title', 'module_code',
                   'instance_code', 'location', 'title', 'promo', 'template', 'last_update', 'last_action')

    #column_filters = (FilterLike(Project.module_title, 'module_title'), 'module_code', 'location')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ProjectModelView, self).__init__(Project, session, **kwargs)

class TemplateModelView(ModelView):
    can_delete = False
    def is_accessible(self):
            #if not is_authenticated():
            #    logging.error("is_accessible: Not authenticated")
            #    return redirect("/")
            return is_authenticated()
    # Override displayed fields
    column_list = ('codemodule', 'slug', 'repository_name', 'call_moulitriche', 'call_judge',
                   'school')

    form_create_rules = ('codemodule', 'slug', 'repository_name', 'call_moulitriche', 'call_judge', 'judge_uri', 'judge_rule',
                    'judge_preliminary_exec', 'judge_final_exec', 'school')
    form_edit_rules = ('repository_name', 'call_moulitriche', 'call_judge', 'judge_uri', 'judge_rule',
                    'judge_preliminary_exec', 'judge_final_exec', 'school')

    column_searchable_list = ('codemodule', 'slug', 'repository_name')

    column_filters = [
        #FilterInList(Template.school, 'school'),
        #FilterLike(Template.codemodule, 'codemodule')
    ]

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(TemplateModelView, self).__init__(Template, session, **kwargs)

class TaskModelView(ModelView):
    can_delete = False
    def is_accessible(self):
            #if not is_authenticated():
            #    logging.error("is_accessible: Not authenticated")
            #    return redirect("/")
            return is_authenticated()
    # Override displayed fields
    column_list = ('type', 'launch_date', 'status',
                   'project')


    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(TaskModelView, self).__init__(Task, session, **kwargs)


class Current(BaseView):

    def project(self, _id):
        obj = db.session.query(Project).get(_id)
        logs = db.session.query(Project_Student).join(Project).filter(Project.id == _id)\
            .join(User).filter(Project_Student.status!=None).order_by(User.login).all()
        success = db.session.query(Project_Student).join(Project).filter(Project.id == _id)\
            .join(User).filter(Project_Student.status=="Succeed").count()
        resp = ["%s %s" % (u.firstname, u.lastname) for u in obj.resp]
        template_resp = ["%s %s" % (u.firstname, u.lastname) for u in obj.template_resp]
        assistants = ["%s %s" % (u.firstname, u.lastname) for u in obj.assistants]
        return self.render("project.html", _id =_id, project=obj, logs=logs, success=success, resp=", ".join(resp),
                           template_resp=", ".join(template_resp), assistants=", ".join(assistants))

    def template(self, _id):
        #projects = db.session.query(Project).join(Project.template).filter(Template.id==_id).all()
        obj = db.session.query(Template).get(_id)
        current = db.session.query(Project).join(Project.template).filter(Template.id == _id)\
            .filter(Project.deadline>=datetime.now()).order_by(Project.location).all()
        past = db.session.query(Project).join(Project.template).filter(Template.id == _id)\
            .filter(Project.deadline<=datetime.now()).order_by(Project.location).all()
        pnames = {}
        mtitle = ""
        for p in current:
            if p.title not in pnames:
                pnames[p.title] = 0
            pnames[p.title] += 1
            mtitle = p.module_title
        for p in past:
            if p.title not in pnames:
                pnames[p.title] = 0
            pnames[p.title] += 1
            mtitle = p.module_title
            success = db.session.query(Project_Student).join(Project).filter(Project.id == p.id)\
            .join(User).filter(Project_Student.status=="Succeed").count()
            p.success = "%0.2f" % float(success * 100 / len(p.students))

        pname = max(pnames.keys(), key=lambda key: pnames[key])
        return self.render("projects.html", _id =_id, tpl = obj, current=current, past=past, module_title=mtitle,
                           project_name=pname)

    @auth.login_required
    @expose('/')
    def index(self):
        if "template_id" in request.args:
            return self.template(request.args.get("template_id"))
        if "project_id" in request.args:
            return self.project(request.args.get("project_id"))
        #arr = db.session.query(Project).filter(Project.deadline>=datetime.now()).all()
        templates = db.session.query(Template).join(Template.projects).group_by(Template.id).filter(Project.deadline>=datetime.now()).all()
        datas = []
        for template in templates:
            d = {}
            projects = db.session.query(Project).join(Project.template).filter(Template.id == template.id).order_by(Project.deadline).all()
            #d["groups"] = 0
            for proj in projects:
                d["min_deadline"] = proj.deadline if "min_deadline" not in d or proj.deadline < d["min_deadline"] \
                    else d["min_deadline"]
                d["max_deadline"] = proj.deadline if "max_deadline" not in d or proj.deadline > d["max_deadline"] \
                    else d["max_deadline"]
                d["project"] = proj.title
                d["module"] = proj.module_title
                #d["groups"] += len(proj.students)
            d["deadline"] = d["max_deadline"]
            d["slug"] = "%s/%s" % (template.codemodule, template.slug)
            if d["min_deadline"] != d["max_deadline"]:
                d["deadline"] = "%s < x < %s" % (d["min_deadline"], d["max_deadline"])
            print("%s > %s" % (template, d["deadline"]))
            d["cities"] = len(projects)
            d["id"] = template.id
            datas.append(d)
        datas = sorted(datas, key= lambda d: d["min_deadline"])
        return self.render("project_current.html", current_templates = datas)

class Past(Current):
    @auth.login_required
    @expose('/')
    def index(self):
        if "template_id" in request.args:
            return self.template(request.args.get("template_id"))
        if "project_id" in request.args:
            return self.project(request.args.get("project_id"))
        templates = db.session.query(Template).join(Template.projects).group_by(Template.id).filter(Project.deadline<datetime.now()).order_by(Project.deadline).all()
        datas = []
        for template in templates:
            d = {}
            projects = db.session.query(Project).join(Project.template).filter(Template.id == template.id).order_by(Project.deadline).all()
            #d["groups"] = 0
            for proj in projects:
                d["min_deadline"] = proj.deadline if "min_deadline" not in d or proj.deadline < d["min_deadline"] \
                    else d["min_deadline"]
                d["max_deadline"] = proj.deadline if "max_deadline" not in d or proj.deadline > d["max_deadline"] \
                    else d["max_deadline"]
                d["project"] = proj.title
                d["module"] = proj.module_title
                #d["groups"] += len(proj.students)
            d["deadline"] = d["max_deadline"]
            d["slug"] = "%s/%s" % (template.codemodule, template.slug)
            if d["min_deadline"] != d["max_deadline"]:
                d["deadline"] = "%s < x < %s" % (d["min_deadline"], d["max_deadline"])
            print("%s > %s" % (template, d["deadline"]))
            d["cities"] = len(projects)
            d["id"] = template.id
            datas.append(d)
        datas = sorted(datas, key= lambda d: d["min_deadline"], reverse=True)
        return self.render("project_current.html", current_templates = datas)



admin = Admin(app, name="Ramassage2", index_view=AdminIndexView(), base_template='layout.html', template_mode='bootstrap3')

admin.add_view(Current(name='Current Projects', menu_icon_type='glyph', menu_icon_value='glyphicon-forward'))
admin.add_view(Past(name='Past Projects', menu_icon_type='glyph', menu_icon_value='glyphicon-backward'))
#admin.add_view(UserModelView(db.session))
#admin.add_view(ProjectModelView(db.session))
admin.add_view(TaskModelView(db.session))
admin.add_view(TemplateModelView(db.session))

if __name__ == "__main__":
    app.run()
