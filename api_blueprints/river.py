__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task
import logging
import json
from datetime import datetime
from api_tools import intranet_auth
from tasks import fetch
river = Blueprint('river', __name__)


@river.route('/', methods=["GET"])
@intranet_auth()
def api_get_river():
    token = request.args["token"]
    fetch.delay(token)
    return jsonify({"status": "Success", "token": str(token)})



#TODO: river, auth_intra, auth_api, manual
