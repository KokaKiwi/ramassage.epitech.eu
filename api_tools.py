__author__ = 'steven'

from flask import request
from functools import wraps
import config
import hashlib
import time
import datetime
import email.utils as eut
import pytz
import base64
import hmac
import logging

def intranet_auth():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from api import api_return_error
            if "token" not in request.args or "sign" not in request.args:
                return api_return_error(400, "Bad request")
            token = request.args["token"]
            sign = request.args["sign"]
            res = hashlib.sha1("{0}-{1}".format(token, config.INTRA_RIVER_SALT).encode("utf-8")).hexdigest()
            if not token or len(token) < 36:
                return api_return_error(400, "Bad request", "This token is invalid")
            if res != sign:
                return api_return_error(403, "Not allowed")
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def signed_auth():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from api import api_return_error
            if "Authorization" in request.headers:
                if "Date" not in request.headers:
                    return api_return_error(400, "Bad Request", "Date missing")
                timestamp = int(time.mktime(eut.parsedate(request.headers["Date"])))
                d_now = datetime.datetime.now(pytz.timezone('Europe/Paris'))
                now = time.mktime(d_now.timetuple())
                if abs(int(now) - timestamp) > 60 * 15:
                    return api_return_error(400, "Bad Request", "Time screw")
                auth = request.headers["Authorization"].split(" ")
                if "Sign" not in auth[0]:
                    return api_return_error(400, "Bad Request", "Wrong auth method")
                tup = base64.b64decode(auth[1]).decode("utf-8").split(":")
                uuid = "base"
                if len(tup) >= 2:
                    logging.warning("Master mode: %s" % (tup[0]))
                    uuid = tup[0]
                    signature = tup[1]
                else:
                    signature = tup[0]
                data = request.data
                if request.method != "POST":
                    data = request.path
                hm = hmac.new(config.API_SALT[uuid].encode("utf-8"), "{0}-{1}".format(str(timestamp), data).encode("utf-8"), hashlib.sha256).hexdigest()
                if hm == signature:
                    return f(*args, **kwargs)
                logging.warning("Signature header: %s" % signature)
                logging.warning("data: [%s]" % (data))
                logging.warning("Signature calcul: %s" % hm)
            return api_return_error(403, "Not allowed", "Signature mismatch")
        return wrapped
    return wrapper