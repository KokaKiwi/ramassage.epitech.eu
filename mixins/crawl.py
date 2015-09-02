__author__ = 'steven'

import requests, json
from exceptions import NotImplemented, UnknownActivity
import config
import logging
import hashlib
import os


class CrawlerMixin(object):
    def __init__(self):
        pass

    def _bigint_json(self, data):
        cleaned = ""
        for line in data.decode('utf-8').split("\n"):
            if not line.startswith('//'):
                cleaned += line
        return json.loads(cleaned)

    def _raw_get(self, url, params=None, content_type="application/json", safe=False, verify=True):
        try:
            obj = requests.get(url, params=params, verify=verify)
            if content_type == "application/json":
                return obj.status_code, obj.json()
            elif content_type == "application/bigintjson":
                return obj.status_code, self._bigint_json(obj.content)
            return obj.status_code, obj.content
        except Exception as e:
            if safe:
                return 500, str(e)
            raise e

    def _raw_post(self, url, datas=None, content_type="application/x-www-form-urlencoded",
                  response_type="application/json", headers={}, safe=False, verify=True):
        try:
            headers['content-type'] = content_type
            obj = requests.post(url, data=datas, headers=headers, verify=verify)
            if response_type == "application/json":
                return obj.status_code, obj.json()
            elif response_type == "application/bigintjson":
                return obj.status_code, self._bigint_json(obj.content)
            return obj.status_code, obj.content
        except Exception as e:
            if safe:
                return 500, str(e)
            raise e

    def _get(self, a, token=""):
        logging.debug("CrawlerMixin::_get action(%s), token(%s)" % (a, token))
        sign = hashlib.sha1("{0}-{1}".format(token, config.CRAWLER_SALT).encode("utf-8")).hexdigest()
        url = config.CRAWLER_URL % {"action": a, "token": token, "sign": sign}
        status_code, data = self._raw_get(url, content_type="application/bigintjson", safe=True)
        if status_code != 200:
            logging.warning("CrawlerMixin::_get action(%s), token(%s) : %s - %s" % (a, token, status_code, data))
            return None
        return data

    def _post_notes(self, token, notes):
        up = {}
        for values in notes:
            key = values["login"]
            up["notes[%s][note]" % key] = values["note"]
            up["notes[%s][commentaire]" % key] = values["comment"]
            if len(up) >= 100:
                self._post("/upload", token, up)
                up = {}
        if len(up) > 0:
            self._post("/upload", token, up)

    def _post(self, a, token, datas):
        logging.warning("CrawlerMixin::_post action(%s), token(%s), datas(%s)" % (a, token, datas))
        sign = hashlib.sha1("{0}-{1}".format(token, config.CRAWLER_SALT).encode("utf-8")).hexdigest()
        url = config.CRAWLER_URL % {"action": a, "token": token, "sign": sign}
        status_code, data = self._raw_post(url, datas, response_type="application/bigintjson", safe=True, verify=False)
        if status_code != 200:
            logging.warning("CrawlerMixin::_post action(%s), token(%s) : %s - %s" % (a, token, status_code, data))
            return None
        return data

    def _inform(self, url, task, optional=None):
        datas = {
            "project_name": task["real_name"] if "real_name" in task else task["slug"],
            "project_code": task["slug"],
            "semester": "B%s" % (task["codeinstance"].split('-')[1] if "codeinstance" in task and len(task["codeinstance"].split("-")) > 0 else 0),
            "module_name": task["module_title"] if "module_title" in task else task["codemodule"],
            "module_code": task["codemodule"],
            "promotion": task["promo"] if "promo" in task else "2013",
            "project_end_date": task["deadline"] if task["deadline"] and len(task["deadline"]) != 0
                                                    and not task["deadline"].startswith("0000") else task["end"],
            }
        if optional:
            datas.update(optional)
        logging.warning(datas)
        status, content = self._raw_post(url, datas, response_type="application/json", verify=False, safe=True)
        if status != 200:
            logging.warning("CrawlerMixin::_inform: url(%s) status(%s) reason(%s)" % (url, status, content))
            return False
        return True

    def inform_triche(self, task):
        opt = {"project_path": os.path.join('/', config.DISTRIBUTE_DIR_IN_JAIL % task)}
        return self._inform(config.TRICHE_URL, task, opt)

    def inform_callback(self, task, url):
        opt = {"project_path": config.DISTRIBUTE_DIR_IN_JAIL % task,
               "correction_path": config.CORRECTION_DIR_IN_JAIL % task}
        return self._inform(url, task, opt)


    def _crawl_activity(self, token):
        def _get_logins(obj, key):
            ret = []
            if not obj or len(obj) == 0:
                return ret
            for elem in obj[key]:
                ret.append({"login": elem["login"], "firstname": elem["title"].split(" ")[0],
                            "lastname": elem["title"].split(" ")[1], "title": elem["title"]})
            return ret

        _conversion = {"0": 5, "1": 5, "2": 5,
                       "3": 4, "4": 4,
                       "5": 3, "6": 3,
                       "7": 2, "8": 2,
                       "9": 1, "10": 1}

        base = self._get("/", token)
        if not base:
            raise UnknownActivity()
        groups = self._get("/registered", token)
        profs = self._get("/prof", token)
        users = []
        clean_groups = []
        for group in groups:
            if not group["master"]["login"] in users:
                g = []
                m = {"login": group["master"]["login"], "firstname": group["master"]["title"].split(" ")[0],
                          "lastname": group["master"]["title"].split(" ")[1], "title": group["master"]["title"]}
                users.append(m)
                g.append(m)
                if "members" in group:
                    for member in group["members"]:
                        g.append({"login": member["login"], "firstname": member["title"].split(" ")[0],
                                  "lastname": member["title"].split(" ")[1], "title": member["title"]})
                clean_groups.append(g)

        result = {
            "token": token,
            "scolaryear": base["scolaryear"],
            "codemodule": base["codemodule"],
            "module_code": base["codemodule"],
            "instance_location": base["instance_location"],
            "location": base["instance_location"],
            "deadline": base["deadline"] if base["deadline"] != None and len(base["deadline"]) != 0
                                            and base["deadline"].startswith("0000") == False else base["end"],
            "slug": base["slug"],
            "resp": _get_logins(profs, "resp"),
            "template_resp": _get_logins(profs, "template_resp"),
            "assistants": _get_logins(profs, "assistant"),
            "students": users,
            "groups": clean_groups,
            "promo": int(base["scolaryear"]) + _conversion[base["codeinstance"].split("-")[1]]
            }
        if "codeinstance" in base:
            result["codeinstance"] = base["codeinstance"]
            result["instance_code"] = base["codeinstance"]
        if "module_title" in base:
            result["module_title"] = base["module_title"]
        if "project_title" in base:
            result["title"] = base["project_title"]
        if "title" in base and len(base["title"]) > 0:
            result["title"] = base["title"]
        return result
