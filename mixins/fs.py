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

    def _archive(self, path, archive_name, root_dir, versioned=False, _format="zip"):
        logging.debug("_archive:: %s.zip < %s" % (archive_name, root_dir))
        if not path:
            self._makedirs(path)
        archive_name = os.path.join(path, archive_name)
        if versioned:
            archive_name = self._new_version("%s.%s" % (archive_name, _format))
        return shutil.make_archive(os.path.join(path, archive_name),  _format, root_dir)


    def _new_version(self, filename):
        if os.path.isfile(filename):
            file_spec, ext = os.path.splitext(filename)
            n, e = os.path.splitext(file_spec)
            try:
                 num = int(e)
                 root = n
            except ValueError:
                 root = file_spec
            _max = 0
            base = os.path.basename(root)
            for file in os.listdir(os.path.dirname(filename)):
                if file.startswith(base) and len(file.split(".")) >= 3 and file.endswith(ext):
                    try:
                        v = int(file.split(".")[1])
                        if v > _max:
                            _max = v
                    except ValueError:
                        pass
            return '%s.%03d%s' % (root, _max + 1, ext)
        return filename

    """def _new_version(self, filename):
        if os.path.isfile(filename):
            file_spec, ext = os.path.splitext(filename)
            n, e = os.path.splitext(file_spec)
            try:
                 num = int(e)
                 root = n
            except ValueError:
                 root = file_spec
            # Find next available file version
            for i in range(1000):
                new_file = '%s.%03d' % (root, i)
                if not os.path.isfile("%s%s" % (new_file, ext)):
                    return "%s%s" % (new_file, ext)
        return filename
    """

    def _last_version(self, filename):
        return filename