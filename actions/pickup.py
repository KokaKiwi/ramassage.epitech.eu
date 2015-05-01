__author__ = 'steven'

from mixins.scm import GitMixin
from exceptions import RepositoryNameMissing
import logging
import os
import config

class Pickup(GitMixin):
    def __init__(self, task_id, project):
        self._project = project
        self._task_id = task_id

    def one(self, login):
        if not self._project["template"]["repository_name"] or len(self._project["template"]["repository_name"]) == 0:
            raise RepositoryNameMissing()
        logging.info("Pickup.one(%s)" % (login))
        succeed, repo = self._retrieve_repository(login, self._project["template"]["repository_name"],
                                  self._task_id, self._project["city"])
        print(repo._messages)
        return succeed

    def clean_all(self):
        if not self._project["template"]["repository_name"] or len(self._project["template"]["repository_name"]) == 0:
            raise RepositoryNameMissing()
        self._remove_all_repository(self._task_id, self._project["template"]["repository_name"])

    def archive(self):
        repos_uri = os.path.join(config.REPOS_DIR, "%(task_id)s/%(repos)s" %
                                 {"task_id": self._task_id, "repos": self._project["template"]["repository_name"]})
        return self._archive(config.ARCHIVE_DIR, "%s-%s" % (self._project["title"], self._project["city"]),
                      repos_uri, versioned=True)