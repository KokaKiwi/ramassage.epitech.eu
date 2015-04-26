__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task, User
import logging
import json
from datetime import datetime

project = Blueprint('project', __name__)

@project.route('/', methods=["GET"])
def api_get_projects():
    from api import db, api_return_error
    try:
        projects = db.session.query(Project).all()
    except Exception as e:
        return api_return_error(500, "Server error", str(e))
    return jsonify({"projects": [p.serialize for p in projects]}), 200


@project.route('/', methods=["POST"])
def api_post_project():
    # module_code, slug, token, scolaryear,
    # module_title, module_code, instance_code,
    # location, title, deadline, promo
    # groups, students, resp, template_resp, assistants
    from api import db, api_return_error
    try:
        datas = request.json

        tpl = db.session.query(Template).filter_by(codemodule=datas["module_code"], slug=datas["slug"]).first()
        if not tpl:
            tpl = Template(codemodule=datas["module_code"], slug=datas["slug"])
            # repository_name, call*, school, ...
            db.session.add(tpl)
        t = Project(template=tpl,
                    token=datas["token"],
                    scolaryear=datas["scolaryear"],
                    module_title=datas["module_title"],
                    module_code=datas["module_code"],
                    instance_code=datas["instance_code"],
                    location=datas["location"],
                    title=datas["title"],
                    deadline=datetime.strptime(datas["deadline"], "%Y-%m-%d %H:%M:%S"),
                    promo=datas["promo"],
                    last_update=datetime.now(),
                    groups=json.dumps(datas["groups"]))
        resp = []
        for user in datas["resp"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            resp.append(u)
        t.resp = resp
        template_resp = []
        for user in datas["template_resp"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            template_resp.append(u)
        t.template_resp = template_resp
        assistants = []
        for user in datas["assistants"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            assistants.append(u)
        t.assistants = assistants

        for user in datas["students"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            t.students.append(Project_Student(user=u, project=t))

        db.session.add(t)
        db.session.add(Task(type="auto", launch_date=t.deadline, project=t))
        #db.session.add(Task(type="preliminary", launch_date=project.deadline - datetime.timedelta(days=1), project=project))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return api_return_error(409, "Conflict", str(e))
    except KeyError as e:
        return api_return_error(400, "Bad Request", "Field %s is missing" % str(e))
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(t.serialize), 201


@project.route('/<int:_id>', methods=["GET"])
def api_get_project(_id):
    from api import db, api_return_error
    try:
        p = db.session.query(Project).get(_id)
        if not p:
            return api_return_error(404, "Project #%s not found" % _id)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(p.serialize), 200

@project.route('/<string:token>', methods=["GET"])
def api_get_project_token(token):
    from api import db, api_return_error
    try:
        p = db.session.query(Project).filter_by(token=token).first()
        if not p:
            return api_return_error(404, "Project #%s not found" % token)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(p.serialize), 200


@project.route('/slug/<string:slug>', methods=["GET"])
def api_get_project_slug(slug):
    from api import db, api_return_error
    try:
        projects = db.session.query(Project).join(Project.template).filter(Template.slug==slug).all()
        if not projects:
            return api_return_error(404, "Slug %s not found" % slug)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify({"projects": [p.serialize for p in projects]}), 200


@project.route('/<int:_id>', methods=["PUT"])
def api_put_project(_id):
    from api import db, api_return_error
    try:
        datas = request.json

        t = db.session.query(Project).get(_id)

        t.token = datas["token"]
        t.scolaryear = datas["scolaryear"]
        t.module_title = datas["module_title"]
        t.module_code = datas["module_code"]
        t.instance_code = datas["instance_code"]
        t.location = datas["location"]
        t.title = datas["title"]
        t.deadline = datetime.strptime(datas["deadline"], "%Y-%m-%d %H:%M:%S")
        t.promo = datas["promo"]
        t.groups = json.dumps(datas["groups"])
        t.last_update = datetime.now()
        resp = []
        for user in datas["resp"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            resp.append(u)
        t.resp = resp
        template_resp = []
        for user in datas["template_resp"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            template_resp.append(u)
        t.template_resp = template_resp
        assistants = []
        for user in datas["assistants"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            assistants.append(u)
        t.assistants = assistants
        t.students = []
        for user in datas["students"]:
            u = db.session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                db.session.add(u)
            t.students.append(Project_Student(user=u, project=t))

        db.session.add(t)
        for task in t.tasks:
            if task.type == "auto":
                task.launch_date = t.deadline
                db.session.add(task)
        #db.session.add(Task(type="preliminary", launch_date=project.deadline - datetime.timedelta(days=1), project=project))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return api_return_error(409, "Conflict", str(e))
    except KeyError as e:
        return api_return_error(400, "Bad Request", "Field %s is missing" % str(e))
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(t.serialize), 200


@project.route('/<int:_id>', methods=["PATCH"])
def api_patch_project(_id):
    from api import db, api_return_error
    try:
        datas = request.json

        t = db.session.query(Project).get(_id)

        for k, v in datas.items():
            if k in ("token", "scolaryear", "module_title", "instance_code", "location",
                     "title", "promo"):
                setattr(t, k, v)

        #"module_code", "slug", deadline, groups
        if ("module_code" in datas and t.module_code != datas["module_code"]) or (
                        "slug" in datas and t.template.slug != datas["slug"]):
            slug = datas["slug"] if "slug" in datas else t.template.slug
            module_code = datas["module_code"] if "module_code" in datas else t.module_code
            tpl = db.session.query(Template).filter_by(codemodule=module_code, slug=slug).first()
            if not tpl:
                tpl = Template(codemodule=module_code, slug=slug)
                db.session.add(tpl)
            t.module_code = module_code
            t.template = tpl
        if "deadline" in datas:
            t.deadline = datetime.strptime(datas["deadline"], "%Y-%m-%d %H:%M:%S")
            for task in t.tasks:
                if task.type == "auto":
                    task.launch_date = t.deadline
                    db.session.add(task)

        if "groups" in datas:
            t.groups = json.dumps(datas["groups"])
        t.last_update = datetime.now()
        if "resp" in datas:
            resp = []
            for user in datas["resp"]:
                u = db.session.query(User).filter_by(login=user["login"]).first()
                if not u:
                    u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                    db.session.add(u)
                resp.append(u)
            t.resp = resp
        if "template_resp" in datas:
            template_resp = []
            for user in datas["template_resp"]:
                u = db.session.query(User).filter_by(login=user["login"]).first()
                if not u:
                    u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                    db.session.add(u)
                template_resp.append(u)
            t.template_resp = template_resp
        if "assistants" in datas:
            assistants = []
            for user in datas["assistants"]:
                u = db.session.query(User).filter_by(login=user["login"]).first()
                if not u:
                    u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                    db.session.add(u)
                assistants.append(u)
            t.assistants = assistants
        if "students" in datas:
            t.students = []
            for user in datas["students"]:
                u = db.session.query(User).filter_by(login=user["login"]).first()
                if not u:
                    u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                    db.session.add(u)
                t.students.append(Project_Student(user=u, project=t))

        db.session.add(t)
        #db.session.add(Task(type="preliminary", launch_date=project.deadline - datetime.timedelta(days=1), project=project))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return api_return_error(409, "Conflict", str(e))
    except KeyError as e:
        return api_return_error(400, "Bad Request", "Field %s is missing" % str(e))
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(t.serialize), 200