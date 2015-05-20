__author__ = 'steven'

from .fs import FsMixin
from .execution import ExecMixin
from exceptions import NotImplemented
import logging
import config
import os
import time


class GitRepository(FsMixin):
    def __init__(self, local_uri, uri, city=None):
        self._local_uri = local_uri
        self._uri = uri
        self._city = city
        self._messages = ""
        self._status = None
        self._date = None

    def clone(self):
        logging.debug("GitRepository::clone uri(%s), local_uri(%s)" % (self._uri, self._local_uri))
        if os.path.exists(self._local_uri) and os.listdir(self._local_uri):
            logging.warning("GitRepository::clone local_uri(%s) not empty" % (self._local_uri))
            self._rmtree(self._local_uri, True)
            #return False
        self._date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        res = self._safe_exec(["git", "clone", "--depth", str(config.GIT_MAX_DEPTH), self._uri, self._local_uri], timeout=config.GIT_CLONE_TIMEOUT)
        if res.return_code == 0:
            self._status = "Success"
            self._messages += "OK. "
            return True
        self._messages += "%s. " % (str(res.exception) if res.exception else res.errs.decode("utf-8"))
        self._status = "Fail"
        return False

    def clone_with_retries(self, count=3):
        for i in range(count):
            self.remove()
            self._messages += "[%s/%s] " % (i, count)
            if self.clone():
                return True
            time.sleep(0.2)
        return False

    def exists(self):
        return os.path.exists(os.path.join(self._local_uri, ".git"))

    def succeed(self):
        return self._status == "Success"

    def pull(self):
        raise NotImplemented()

    def checkout(self, branch):
        raise NotImplemented()

    def infos(self): # generate .pickup
        if not os.path.exists(self._local_uri):
            self._makedirs(self._local_uri, True)
        with open(os.path.join(self._local_uri, ".pickup"), "w") as f:
            res = self._safe_exec("git config --get remote.origin.url", cwd=self._local_uri)
            f.write("Repo: %s\n" % (res.outs.decode("utf-8").replace("\r", "").replace("\n", "")))
            f.write("City: %s\n" % self._city)
            f.write("Status: %s\n" % self._status)
            f.write("Logs: %s\n" % self._messages)
            f.write("Date: %s\n" % self._date)
            f.write("Remote Branches:\n")
            res = self._safe_exec("git branch -r", cwd=self._local_uri)
            f.write(res.outs.decode("utf-8"))
            f.write("Local Branches:\n")
            res = self._safe_exec("git branch", cwd=self._local_uri)
            f.write(res.outs.decode("utf-8"))
            f.write("Git graph && Last commit:\n")
            res = self._safe_exec("git log --graph --pretty=medium -n 5", cwd=self._local_uri)
            f.write(res.outs.decode("utf-8"))


    def clean(self):
        self._rmtree(os.path.join(self._local_uri, ".git"), safe=True)

    def remove(self):
        if os.path.exists(self._local_uri):
            self._rmtree(self._local_uri, safe=True)

class GitMixin(FsMixin):
    def __init__(self):
        pass

    def _retrieve_repository_(self, local_uri, uri, city=None):
        obj = GitRepository(local_uri, uri, city)
        obj.clone_with_retries()
        obj.infos()
        obj.clean()
        return obj.succeed(), obj

    def _retrieve_repository(self, student, repository_name, task_id, city):
        local_uri = os.path.join(config.REPOS_DIR, "%(task_id)s/%(repos)s/%(stud)s" % {"task_id": task_id, "repos": repository_name, "stud": student})
        uri = config.REPOS_URI % {"repos": repository_name, "stud": student}
        return self._retrieve_repository_(local_uri, uri, city)

    def _remove_repository_(self, local_uri):
        obj = GitRepository(local_uri, "")
        return obj.remove()

    def _remove_repository(self, student, repository_name, task_id):
        local_uri = os.path.join(config.REPOS_DIR, "%(task_id)s/%(repos)s/%(stud)s" % {"task_id": task_id, "repos": repository_name, "stud": student})
        return self._remove_repository_(local_uri)

    def _remove_all_repository(self, task_id, repository_name):
        local_uri = os.path.join(config.REPOS_DIR, "%(task_id)s/%(repos)s" % {"task_id": task_id, "repos": repository_name})
        return self._rmtree(local_uri, safe=True)
