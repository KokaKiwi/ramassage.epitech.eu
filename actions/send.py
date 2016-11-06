__author__ = 'steven'

from mixins.scm import FsMixin
from exceptions import FileMissing
import logging
import os
import config

class SendFile(FsMixin):
    def __init__(self, project):
        self._project = project

    def path(self):
        archive_name = os.path.join(config.ARCHIVE_DIR, self._cleanfilename("%s-%s" % (
            self._project["title"], self._project["instance_code"])))
        filename = self._last_version("%s.zip" % (archive_name), with_extension=True)
        logging.warning(filename)
        if not os.path.isfile(filename):
            raise FileMissing()
        filename = os.path.basename(filename)
        filepath = config.ARCHIVE_DIR
        return filepath, filename
