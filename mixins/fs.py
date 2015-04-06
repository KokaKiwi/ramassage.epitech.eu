__author__ = 'steven'

import os, errno, shutil, stat, logging


class FsMixin(object):
    def __init__(self):
        pass

    def _makedirs(self, path, safe=False):
        try:
            logging.debug("_makedirs: %s" % path)
            os.makedirs(path, exist_ok=True)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                if safe:
                    return False
                raise exc
        return True

    def _rmtree(self, path, safe=False):
        def force_remove(function, path, excinfo):
            logging.debug("force_remove: %s" % path)
            excvalue = excinfo[1]
            if function in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
                # change the file to be readable,writable,executable: 0777
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                # retry
                function(path)
            else:
                raise
        try:
            logging.debug("_rmtree: %s" % path)
            shutil.rmtree(path, ignore_errors=False, onerror=force_remove)
        except Exception as e:
            if safe:
                return False
            raise e
        return True
