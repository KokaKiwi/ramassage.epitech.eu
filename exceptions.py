__author__ = 'steven'


class NotImplemented(Exception):
    def __init__(self, msg='This feature is not yet implemented'):
        self.msg = msg

    def __str__(self):
        return self.msg


class UnknownActivity(Exception):
    def __init__(self, msg='This activity doesn\'t exist'):
        self.msg = msg

    def __str__(self):
        return self.msg


class FieldsMissing(Exception):
    def __init__(self, msg='Fields are missing'):
        self.msg = msg

    def __str__(self):
        return self.msg
