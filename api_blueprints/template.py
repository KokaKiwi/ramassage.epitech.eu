__author__ = 'steven'


from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
import logging
from models import Template

template = Blueprint('template', __name__)

from api_tools import signed_auth


@template.route('/', methods=["GET"])
@signed_auth()
def api_get_templates():
    from api import db, api_return_error
    try:
        templates = db.session.query(Template).all()
    except Exception as e:
        return api_return_error(500, "Server error", str(e))
    return jsonify({"templates": [t.serialize for t in templates]}), 200


@template.route('/', methods=["POST"])
@signed_auth()
def api_post_template():
    from api import db, api_return_error
    try:
        datas = request.json
        t = Template(codemodule=datas["codemodule"], slug=datas["slug"])
        for k, v in datas.items():
            if k in ("repository_name", "call_moulitriche", "call_judge", "judge_uri",
                     "judge_rule", "judge_preliminary_exec", "judge_final_exec", "school"):
                setattr(t, k, v)
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


@template.route('/<int:_id>', methods=["GET"])
@signed_auth()
def api_get_template(_id):
    from api import db, api_return_error
    try:
        u = db.session.query(Template).get(_id)
        if not u:
            return api_return_error(404, "Template #%s not found" % _id)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify(u.serialize), 200


@template.route('/<string:slug>', methods=["GET"])
@template.route('/slug/<string:slug>', methods=["GET"])
@signed_auth()
def api_get_template_slug(slug):
    from api import db, api_return_error
    try:
        tpls = db.session.query(Template).filter_by(slug=slug).all()
        if not tpls:
            return api_return_error(404, "Slug %s not found" % slug)
    except Exception as e:
        db.session.rollback()
        logging.error(str(e))
        return api_return_error(500, "Server error", str(e))
    return jsonify({"templates": [t.serialize for t in tpls]}), 200


@template.route('/<int:_id>', methods=["PUT", "PATCH"])
@signed_auth()
def api_put_template(_id):
    from api import db, api_return_error
    try:
        datas = request.json
        t = db.session.query(Template).get(_id)
        if not t:
            return api_return_error(404, "Template #%s not found" % _id)
        for k, v in datas.items():
            if k in ("repository_name", "call_moulitriche", "call_judge", "judge_uri",
                     "judge_rule", "judge_preliminary_exec", "judge_final_exec", "school"):
                setattr(t, k, v)
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
