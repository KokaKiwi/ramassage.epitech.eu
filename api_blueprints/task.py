__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task
import logging
import json
from datetime import datetime

task = Blueprint('task', __name__)


@task.route('/', methods=["GET"])
def api_get_task():
    from api import db, api_return_error
    try:
        tasks = db.session.query(Task).all()
    except Exception as e:
        return api_return_error(500, "Server error", str(e))
    return jsonify({"tasks": [t.serialize for t in tasks]}), 200
