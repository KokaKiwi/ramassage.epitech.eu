__author__ = 'steven'

from mixins.crawl import CrawlerMixin
import config


class InformTriche(CrawlerMixin):
    def __init__(self, obj):
        obj["codemodule"] = obj["template"]["slug"]
        obj["slug"] = obj["template"]["slug"]
        obj["login"] = config.TRICHE_LOGIN
        obj["codeinstance"] = obj["instance_code"]
        self.datas = self.inform_triche(obj)

    @property
    def result(self):
        return self.datas
