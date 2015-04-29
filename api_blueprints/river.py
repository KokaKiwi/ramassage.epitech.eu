__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task
import logging
import json
from datetime import datetime
from api_tools import intranet_auth

river = Blueprint('river', __name__)


@river.route('/', methods=["GET"])
@intranet_auth()
def api_get_river():
    return jsonify({})



#TODO: river, auth_intra, auth_api, manual
