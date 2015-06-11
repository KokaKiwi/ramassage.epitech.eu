__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task
import logging
import json
from datetime import datetime

task = Blueprint('task', __name__)

from api_tools import signed_auth, nocache


@task.route('/', methods=["GET"])
@signed_auth()
@nocache
def api_get_tasks():
    from api import db, api_return_error
    try:
        tasks = db.session.query(Task).all()
    except Exception as e:
        return api_return_error(500, "Server error", str(e))
    return jsonify({"tasks": [t.serialize for t in tasks]}), 200


@task.route('/', methods=["POST"])
@signed_auth()
def api_post_task():
    from api import db, api_return_error
    try:
        datas = request.json
        p = db.session.query(Project).get(datas["project_id"])
        if not p:
            return api_return_error(404, "Project not Found")
        if datas["type"] == "auto":
            return api_return_error(403, "Not allowed", "You are not allowed to add an automated Task")
        t = Task(type=datas["type"], launch_date=datetime.strptime(datas["launch_date"], "%Y-%m-%d %H:%M:%S"),
                            project=p, exec_cmd=datas["exec_cmd"], extend=datas["extend"])
        db.session.add(t)
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


@task.route('/<int:_id>', methods=["GET"])
@signed_auth()
@nocache
def api_get_task(_id):
    from api import db, api_return_error
    try:
        t = db.session.query(Task).get(_id)
        if not t:
            return api_return_error(404, "Task #%s not found" % _id)
    except Exception as e:
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(t.serialize), 200


@task.route('/<string:slug>', methods=["GET"])
@signed_auth()
@nocache
def api_get_task_slug(slug):
    from api import db, api_return_error
    try:
        tks = db.session.query(Task).join(Task.project).join(Project.template).filter(Template.slug==slug).all()
        if not tks:
            return api_return_error(404, "Slug #%s not found" % slug)
    except Exception as e:
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify({"tasks": [t.serialize for t in tks]}), 200


@task.route('/project/<int:_id>', methods=["GET"])
@signed_auth()
@nocache
def api_get_task_project(_id):
    from api import db, api_return_error
    try:
        tks = db.session.query(Task).filter_by(project_id=_id).all()
        if not tks:
            return api_return_error(404, "Task #%s not found" % _id)
    except Exception as e:
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify({"tasks": [t.serialize for t in tks]}), 200


@task.route('/<int:_id>', methods=["PUT"])
@signed_auth()
def api_put_task(_id):
    from api import db, api_return_error
    try:
        datas = request.json
        t = db.session.query(Task).get(_id)
        if not t:
            return api_return_error(404, "Task not Found")
        if not t.type == "auto":
            t.launch_date = datetime.strptime(datas["launch_date"], "%Y-%m-%d %H:%M:%S")
            t.type = datas["type"] if datas["type"] != "auto" else t.type
        else:
            if t.type != datas["type"] or t.launch_date != datetime.strptime(datas["launch_date"], "%Y-%m-%d %H:%M:%S"):
                return api_return_error(403, "Not allowed", "You are not allowed to modify an automated task")
        t.exec_cmd = datas["exec_cmd"]
        t.extend = datas["extend"]
        db.session.add(t)
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

@task.route('/<int:_id>', methods=["PATCH"])
@signed_auth()
def api_patch_task(_id):
    from api import db, api_return_error
    try:
        datas = request.json
        t = db.session.query(Task).get(_id)
        if not t:
            return api_return_error(404, "Task not Found")
        if not t.type == "auto":
            if "launch_date" in datas:
                t.launch_date = datetime.strptime(datas["launch_date"], "%Y-%m-%d %H:%M:%S")
            if "type" in datas and datas["type"] != "auto":
                t.type = datas["type"]
        else:
            if ("type" in datas and t.type != datas["type"]) or ("launch_date" in datas
                                                                 and t.launch_date != datetime.strptime(datas["launch_date"], "%Y-%m-%d %H:%M:%S")):
                return api_return_error(403, "Not allowed", "You are not allowed to modify an automated task")
        if "exec_cmd" in datas:
            t.exec_cmd = datas["exec_cmd"]
        if "extend" in datas:
            t.extend = datas["extend"]
        db.session.add(t)
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
