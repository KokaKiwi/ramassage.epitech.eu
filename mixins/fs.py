__author__ = 'steven'

import os, errno, shutil, stat, logging
import config

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
            archive_name = self._new_version("%s.%s" % (archive_name, _format), with_extension=False)
        return shutil.make_archive(os.path.join(path, archive_name),  _format, root_dir)


    def _new_version(self, filename, with_extension=True):
        file_spec, ext = os.path.splitext(filename)
        if os.path.isfile(filename):
            file_spec, ext = os.path.splitext(filename)
            n, e = os.path.splitext(file_spec)
            try:
                 num = int(e)
                 root = n
            except ValueError:
                 root = n
            _max = -1
            base = os.path.basename(root)
            for file in os.listdir(os.path.dirname(filename)):
                if file.startswith(base) and len(file.split(".")) >= 3 and file.endswith(ext):
                    try:
                        v = int(file.split(".")[1])
                        if v > _max:
                            _max = v
                    except ValueError:
                        pass
            return '%s.%03d%s' % (root, _max + 1, ext if with_extension else "")
        return filename if with_extension else file_spec

    def _last_version(self, filename, with_extension=True):
        file_spec, ext = os.path.splitext(filename)
        if os.path.isfile(filename):
            file_spec, ext = os.path.splitext(filename)
            n, e = os.path.splitext(file_spec)
            try:
                 num = int(e)
                 root = n
            except ValueError:
                 root = n
            _max = -1
            base = os.path.basename(root)
            for file in os.listdir(os.path.dirname(filename)):
                if file.startswith(base) and len(file.split(".")) >= 3 and file.endswith(ext):
                    try:
                        v = int(file.split(".")[1])
                        if v > _max:
                            _max = v
                    except ValueError:
                        pass
            if _max == -1:
                return filename
            return '%s.%03d%s' % (root, _max, ext if with_extension else "")
        return filename if with_extension else file_spec

    def _distribute_for_user(self, datas, filepath, filename):
        path = config.DISTRIBUTE_DIR % datas
        if not os.path.exists(path):
            self._makedirs(path, safe=True)
        if os.path.exists(os.path.join(path, filename)):
            os.remove(os.path.join(path, filename))
        os.link(os.path.join(filepath, filename), os.path.join(path, filename))

    def _distribute(self, users, filename, scolaryear, codemodule, slug, filepath=config.ARCHIVE_DIR):
        datas = {
            "scolaryear": scolaryear,
            "codemodule": codemodule,
            "slug": slug,
        }
        for user in users:
            datas["login"] = user
            self._distribute_for_user(datas, filepath, filename)

    def distribute(self, task, filename, filepath=config.ARCHIVE_DIR):
        if "resp" in task and not isinstance(task["resp"], list):
            task["resp"] = [task["resp"]]
        if "template_resp" in task and not isinstance(task["template_resp"], list):
            task["template_resp"] = [task["template_resp"]]
        if "assistants" in task and not isinstance(task["assistants"], list):
                task["assistants"] = [task["assistants"]]
        if "triche" in task and task["triche"]:
            if "template_resp" in task:
                task["template_resp"].append(config.TRICHE_LOGIN)
            else:
                task["template_resp"] = [config.TRICHE_LOGIN]
        if "resp" in task:
            self._distribute(task["resp"], filename, task["scolaryear"], task["codemodule"], task["slug"], filepath)
        if "template_resp" in task:
            self._distribute(task["template_resp"], filename, task["scolaryear"], task["codemodule"], task["slug"], filepath)
        if "assistants" in task:
            self._distribute(task["assistants"], filename, task["scolaryear"], task["codemodule"], task["slug"], filepath)
