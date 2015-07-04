#!/usr/bin/env python3.4
__author__ = 'Steven'

try:
    import httplib
except:
    import http.client as httplib

from optparse import OptionParser
import inspect
import json
import requests
import time
import logging
import hashlib
import hmac
import base64
import os
import uuid
import pytz
import urllib
import datetime
import sys

VERSION = "0.1 beta"


class Controller(object):
    def __init__(self):
        self._options = {}
        self._config = {}
        self._config["URI"] = "127.0.0.1:8080"
        self._config["UUID"] = "93330b53-d676-4e38-a275-4b147798366c"
        self._config["HASH"] = "5b10bd446259b8f2d2be0ae955b32ff9da218e5feab9cc3527819b19fa77e2e9"

    def _sign(self, d, method, url, datas=None):
        if method == "POST":
            data = datas.decode("utf-8") if datas else ""
        else:
            data = url
        print("data: %s" % "{0}-{1}".format(str(int(time.mktime(d.timetuple()))),
            data).encode("utf-8"))
        hm = hmac.new(self._config["HASH"].encode("utf-8"), "{0}-{1}".format(str(int(time.mktime(d.timetuple()))),
            data).encode("utf-8"), hashlib.sha256)

        l = hm.hexdigest() if not self._config["UUID"] else "%s:%s" % (self._config["UUID"], hm.hexdigest())
        return "Sign %s" % base64.b64encode(l.encode("utf-8")).decode("utf-8")

    def _storeFile(self, url, response):
        dir = "."
        url = os.path.join(dir, str(uuid.uuid4()) + ".zip")
        with open(url, 'wb') as f:
            f.write(response.read(65 * 1024))
        return {"file": url}

    def _req(self, method, url, datas=None, data_type="application/json"):
        conn = httplib.HTTPConnection(self._config["URI"])
        headers = {"Content-type": "application/json"}
        d = datetime.datetime.now(pytz.timezone('Europe/Paris'))
        headers["Date"] = d.strftime('%a, %d %b %Y %H:%M:%S %z')
        print("Date: %s" % headers["Date"])
        headers["Authorization"] = self._sign(d, method, url,
                                              json.dumps(datas).encode("utf-8") if data_type == "application/json"
                                              else datas.encode("utf-8"))
        print("Authorization: %s" % headers["Authorization"])
        if data_type == "application/json":
            conn.request(method, url, urllib.parse.urlencode(datas) if datas and method == "GET" else json.dumps(datas).encode("utf-8"), headers=headers)
        else:
            conn.request(method, url, urllib.parse.urlencode(datas) if datas and method == "GET" else datas.encode("utf-8"), headers=headers)
        conn.set_debuglevel(1)
        response = conn.getresponse()
        content_type = response.getheader("Content-Type")
        if response.status > 201:
            print('%s: %s %s' % (url, response.status, response.reason))
        try:
            if content_type.find("zip") >= 0:
                return self._storeFile(url, response)
            return json.loads(response.read().decode())
        except Exception as e:
            print("get Exception: %s" % e)
            return {}

    def _get(self, url):
        return self._req("GET", url)

    def _post(self, url, datas):
        return self._req("POST", url, datas)

    def _delete(self, url):
        return self._req("DELETE", url)

    def _upload(self, url, f, form="PUT"):
        import requests
        print(os.path.basename(f))
        headers = {}
        res = requests.put("http://" + self._machine + url, files={"file": (os.path.basename(f), open(f, 'rb'))},
                           headers=headers)
        print(res.text)

    def _post_notes(self, url, filename):
        raw_datas = ""
        with open(filename, "r") as f:
            raw_datas = f.readlines()
        print(raw_datas)
        return self._req("POST", url, "".join(raw_datas), "text/csv")

    def searchAction(self, slug, *args):
        """Find project(s) by slug"""
        print(self._get("/1.0/project/slug/%s" % slug))
        return True

    def projectAction(self, uid, *args):
        """Show project information"""
        res = self._get("/1.0/project/%s" % uid)
        print(res)
        print(self._beautify_project(res))
        return True

    def _beautify_project(self, obj):
        return """Project #%(id)s
    - Scolaryear: %(scolaryear)s
    - City: %(scolaryear)s
    - Deadline: %(scolaryear)s
    - Module: %(module_title)s (%(module_code)s)
    - Title: %(scolaryear)s
    - Instance: %(instance_code)s
    - Promo: %(scolaryear)s
    - Slug: %(scolaryear)s
""" % (obj)

    """
        Actions interessantes :
            o Programmer un ramassage : soit maintenant, soit à une date precise, pour une seule ville ou plusieurs
             => soit avec l'id du projet, ou le slug, ou le nom ?
            o uploader des notes : soit avec un slug +/- ville(s), soit avec l'id
            o stats sur un ramassage (slug + ville, ou id)
            o recuperer adresses emails pour un projet
            o infos sur un template
            o infos sur un module ?
            o recuperer les projets d'un utilisateur
    """

    @property
    def usage(self):
        ret = "usage: %prog [options] command [params...]\n"
        ret += "Command(s) available:\n"
        for function_name, fn in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            #print("function_name(%s) : fn(%s)" % (function_name, fn))
            if function_name.endswith("Action"):
                ret += "\to %s [%s]\n\t\t%s\n" % (function_name.replace("Action", ""),
                                                ", ".join(inspect.getargspec(fn).args[1:]),
                                                fn.__doc__ if fn.__doc__ else "")
        return ret

    def _execute(self, args):
        cmd = args[0]
        method = "%sAction" % (cmd.lower())
        try:
            for function_name, fn in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
                if method == function_name:
                    result = fn(self, *args[1:])
                    if result == False:
                        sys.exit(1)
                    return True
        except Exception as e:
            print(str(e))
            return True
        sys.stderr.write("%s: Command not found\n\n" % cmd)
        return False

    def execute(self):
        parser = OptionParser(self.usage, version=VERSION)
        parser.add_option("-c", "--config", dest="filename",
                          help="using a specific config file FILE", metavar="FILE")
        parser.add_option("-j", "--json",
                          action="store_true", dest="json",
                          help="display output as json", default=False)
        parser.add_option("-q", "--quiet",
                          action="store_false", dest="verbose", default=True,
                          help="don't print status messages to stdout")

        (self._options, args) = parser.parse_args()
        if len(args) == 0:
            return parser.print_usage()
        print("options: %s" % str(self._options))
        print("args: %s" % str(args))
        if not self._execute(args):
            sys.stderr.write(parser.get_usage())


if __name__ == "__main__":
    Controller().execute()