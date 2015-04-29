__author__ = 'steven'

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from models import User
import logging

user = Blueprint('user', __name__)

from api import db, api_return_error

from api_tools import signed_auth

@user.route('/', methods=["GET"])
@signed_auth()
def api_get_users():
    try:
        users = db.session.query(User).all()
    except Exception as e:
        return api_return_error(500, "Server error", str(e))
    return jsonify({"users": [u.serialize for u in users]}), 200

@user.route('/', methods=["POST"])
@signed_auth()
def api_post_user():
    try:
        datas = request.json
        u = User(firstname=datas["firstname"], lastname=datas["lastname"], login=datas["login"])
        db.session.add(u)
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
    return jsonify(u.serialize), 201

@user.route('/<int:_id>', methods=["GET"])
@signed_auth()
def api_get_user(_id):
    try:
        u = db.session.query(User).get(_id)
        if not u:
            return api_return_error(404, "User #%s not found" % _id)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(u.serialize), 200

@user.route('/<string:login>', methods=["GET"])
@signed_auth()
def api_get_user_login(login):
    try:
        u = db.session.query(User).filter_by(login=login).first()
        if not u:
            return api_return_error(404, "User %s not found" % login)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(u.serialize), 200

@user.route('/<int:id>', methods=["PUT"])
@signed_auth()
def api_put_user(id):
    try:
        datas = request.json
        u = db.session.query(User).get(id)
        if not u:
            return api_return_error(404, "User #%s not found" % id)
        u.firstname = datas["firstname"]
        u.lastname = datas["lastname"]
        u.login = datas["login"]
        db.session.add(u)
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
    return jsonify(u.serialize), 200

@user.route('/<int:id>', methods=["PATCH"])
@signed_auth()
def api_patch_user(id):
    try:
        datas = request.json
        u = db.session.query(User).get(id)
        if not u:
            return api_return_error(404, "User #%s not found" % id)
        for k, v in datas.items():
            setattr(u, k, v)
        db.session.add(u)
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
    return jsonify(u.serialize), 200

@user.route('/<int:id>', methods=["DELETE"])
@signed_auth()
def api_delete_user(id):
    try:
        datas = request.json
        u = db.session.query(User).get(id)
        if not u:
            return api_return_error(404, "User #%s not found" % id)
        db.session.delete(u)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(u.serialize), 200
