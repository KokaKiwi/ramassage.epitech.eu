__author__ = 'steven'

from mixins.crawl import CrawlerMixin

class Fetch(CrawlerMixin):
    def __init__(self, token):
        self.datas = self._crawl_activity(token)

    @property
    def result(self):
        return self.datas
