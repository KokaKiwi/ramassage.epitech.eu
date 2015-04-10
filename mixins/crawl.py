__author__ = 'steven'

import requests, json
from exceptions import NotImplemented, UnknownActivity
import config
import logging
import hashlib


class CrawlerMixin(object):
    def __init__(self):
        pass

    def _bigint_json(self, data):
        cleaned = ""
        for line in data.decode('utf-8').split("\n"):
            if not line.startswith('//'):
                cleaned += line
        return json.loads(cleaned)

    def _raw_get(self, url, params=None, content_type="application/json", safe=False):
        try:
            obj = requests.get(url, params=params)
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
                  response_type="application/json", headers={}, safe=False):
        try:
            headers['content-type'] = content_type
            obj = requests.post(url, data=datas, headers=headers)
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

    def _post(self):
        raise NotImplemented()

    def _crawl_activity(self, token):
        def _get_logins(obj, key):
            ret = []
            if not obj or len(obj) == 0:
                return ret
            for elem in obj[key]:
                ret.append(elem["login"])
            return ret

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
                users.append(group["master"]["login"])
                g.append(group["master"]["login"])
                if "members" in group:
                    for member in group["members"]:
                        g.append(member["login"])
                clean_groups.append(g)
        result = {
            "scolaryear": base["scolaryear"],
            "codemodule": base["codemodule"],
            "instance_location": base["instance_location"],
            "end": base["end"],
            "deadline": base["deadline"],
            "slug": base["slug"],
            "resp": _get_logins(profs, "resp"),
            "template_resp": _get_logins(profs, "template_resp"),
            "assistants": _get_logins(profs, "assistant"),
            "users": users,
            "groups": clean_groups,
            }
        if "codeinstance" in base:
            result["codeinstance"] = base["codeinstance"]
        if "module_title" in base:
            result["module_title"] = base["module_title"]
        if "title" in base:
            result["real_name"] = base["title"]
        return result


