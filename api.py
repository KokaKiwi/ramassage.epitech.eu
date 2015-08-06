__author__ = 'steven'


from flask import request, Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import config

from api_tools import nocache

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_DB_URI
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
try:
    if config.DEBUG:
        app.debug = True
except ImportError:
    pass

cors = CORS(app, resources={r"/1.0/*": {"origins": "*"}}, allow_headers=['Content-Type', 'Date', 'Authorization', 'X-Date'])
db = SQLAlchemy(app)


from api_blueprints.template import template
from api_blueprints.user import user
from api_blueprints.project import project
from api_blueprints.task import task
from api_blueprints.river import river

app.register_blueprint(template, url_prefix='/1.0/template')
app.register_blueprint(user, url_prefix='/1.0/user')
app.register_blueprint(project, url_prefix='/1.0/project')
app.register_blueprint(task, url_prefix='/1.0/task')
app.register_blueprint(river, url_prefix='/1.0/river')

@app.route('/', methods=["GET"])
@nocache
def api_get_root():
    return jsonify({})


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
