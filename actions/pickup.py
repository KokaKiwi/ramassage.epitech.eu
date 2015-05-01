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
        return succeed, repo

    def clean_all(self):
        if not self._project["template"]["repository_name"] or len(self._project["template"]["repository_name"]) == 0:
            raise RepositoryNameMissing()
        self._remove_all_repository(self._task_id, self._project["template"]["repository_name"])

    def archive(self):
        repos_uri = os.path.join(config.REPOS_DIR, "%(task_id)s/%(repos)s" %
                                 {"task_id": self._task_id, "repos": self._project["template"]["repository_name"]})
        arch = self._cleanfilename("%s-%s" % (self._project["title"], self._project["city"]))
        self._archive(config.ARCHIVE_DIR, arch,
                      repos_uri, versioned=True)
        return arch

    def distribute(self):
        archive_name = os.path.join(config.ARCHIVE_DIR, self._cleanfilename("%s-%s" % (
            self._project["title"], self._project["city"])))
        filename = self._last_version("%s.zip" % (archive_name), with_extension=True)
        filename = os.path.basename(filename)
        filepath = config.ARCHIVE_DIR
        if "resp" not in self._project:
            self._project["resp"] = []
        if "template_resp" not in self._project:
            self._project["template_resp"] = []
        if "assistants" not in self._project:
                self._project["assistants"] = []
        if "template_resp" in self._project:
            self._project["template_resp"].append({'lastname': None, 'login': config.TRICHE_LOGIN, 'id': None,
                                                   'firstname': None})
        if "resp" in self._project:
            self._distribute(self._project["resp"], filename, self._project["scolaryear"],
                             self._cleanfilename(self._project["module_title"]),
                             self._cleanfilename(self._project["title"]), filepath)
        if "template_resp" in self._project:
            self._distribute(self._project["template_resp"], filename, self._project["scolaryear"],
                             self._cleanfilename(self._project["module_title"]),
                             self._cleanfilename(self._project["title"]), filepath)
        if "assistants" in self._project:
            self._distribute(self._project["assistants"], filename, self._project["scolaryear"],
                             self._cleanfilename(self._project["module_title"]),
                             self._cleanfilename(self._project["title"]), filepath)
