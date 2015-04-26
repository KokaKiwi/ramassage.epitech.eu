__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import Project, Project_Student, Template, Task
import logging
import json
from datetime import datetime

river = Blueprint('river', __name__)


@river.route('/', methods=["POST"])
def api_post_river():
    pass



#TODO: river, auth_intra, auth_api, manual
