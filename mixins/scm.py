__author__ = 'steven'

from subprocess import call
from .fs import FsMixin
from .execution import ExecMixin
from exceptions import NotImplemented
import logging
import config
import os


class GitRepository(ExecMixin, FsMixin):
    def __init__(self, local_uri, uri):
        self._local_uri = local_uri
        self._uri = uri

    def clone(self):
        logging.debug("GitRepository::clone uri(%s), local_uri(%s)" % (self._uri, self._local_uri))
        if os.path.exists(self._local_uri) and os.listdir(self._local_uri):
            logging.warning("GitRepository::clone local_uri(%s) not empty" % (self._local_uri))
            return False
        res = self._safe_exec(["git", "clone", "--depth", str(config.GIT_MAX_DEPTH), self._uri, self._local_uri], timeout=config.GIT_CLONE_TIMEOUT)
        if res.return_code == 0:
            return True
        return False
        pass

    def exists(self):
        return os.path.exists(os.path.join(self._local_uri, ".git"))

    def pull(self):
        raise NotImplemented()

    def checkout(self, branch):
        raise NotImplemented()

    def infos(self): # generate .pickup
        pass

    def clear(self): # remove .git
        self._rmtree(os.path.join(self._local_uri, ".git"), safe=True)

    def remove(self): # remove local clone
        if os.path.exists(self._local_uri):
            self._rmtree(self._local_uri, safe=True)

class GitMixin(FsMixin):
    def __init__(self):
        pass

    def _retrieve_repository(self, uri, dest_uri):
        # /work/repos/%(task_id)s/%(repository_name)s/%(login)s
        pass

    def _retrieve_repository(self, student, repository_name):
        pass

    def _remove_repository(self):
        pass

    def remove_all_repository(self):
        pass
