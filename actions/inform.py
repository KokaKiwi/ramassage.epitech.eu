__author__ = 'steven'

from mixins.crawl import CrawlerMixin
from mixins.fs import FsMixin
import config


class InformTriche(CrawlerMixin, FsMixin):
    def __init__(self, obj):
        obj["codemodule"] = self._cleanfilename(obj["module_title"])
        obj["slug"] = self._cleanfilename(obj["title"])
        obj["login"] = config.TRICHE_LOGIN
        obj["codeinstance"] = obj["instance_code"]
        self.datas = self.inform_triche(obj)

    @property
    def result(self):
        return self.datas
