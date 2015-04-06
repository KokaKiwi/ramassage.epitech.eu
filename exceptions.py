__author__ = 'steven'


class NotImplemented(Exception):
    def __init__(self, msg='This feature is not yet implemented'):
        self.msg = msg

    def __str__(self):
        return self.msg

