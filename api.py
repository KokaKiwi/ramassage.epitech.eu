__author__ = 'steven'


from flask import request, Flask, jsonify
from sqlalchemy.exc import IntegrityError
#from flask.ext.sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from exceptions import FieldsMissing
import config
import logging
from models import User


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_DB_URI
app.debug = True
db = SQLAlchemy(app)

@app.route('/', methods=["GET"])
def api_get_root():
    try:
        users = db.session.query(User).all()
    except Exception as e:
        logging.error(str(e))
    return jsonify({"users": [u.serialize for u in users]})


@app.route('/1.0/user', methods=["POST"])
def api_post_user():
    try:
        datas = request.json
        #for field in ("firstname", "lastname", "login"):
        #    if field not in datas:
        #        logging.warning("%s missing" % field)
        #        raise FieldsMissing("Fields are missing : i.e %s" % field)
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

@app.route('/1.0/user/<int:_id>', methods=["GET"])
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

@app.route('/1.0/user/<string:login>', methods=["GET"])
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


@app.route('/1.0/user/<int:id>', methods=["PUT"])
def api_put_user(id):
    try:
        datas = request.json
        u = db.session.query(User).get(id)
        if not u:
            return api_return_error(404, "User #%s not found" % id)
        #u = User(firstname=datas["firstname"], lastname=datas["lastname"], login=datas["login"])
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


@app.route('/1.0/user/<int:id>', methods=["PATCH"])
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

@app.route('/1.0/user/<int:id>', methods=["DELETE"])
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


def api_return_error(status_code, title, detail=None, code=None, _id=None):
    message = {
            'status': status_code,
            'title': title,
    }
    if detail:
        message["detail"] = detail
    if code:
        message["code"] = code
    if _id:
        message["id"] = _id
    resp = jsonify(message)
    resp.status_code = status_code
    return resp

@app.errorhandler(404)
def not_found(error=None):
    return api_return_error(404, "File Not Found: %s" % request.path)

if __name__ == "__main__":
    app.run()
