__author__ = 'Steven'

from mixins.execution import ExecMixin, ExecResult
from mixins.fs import FsMixin
import logging
import os
import config
import csv


class CPoolDriver(FsMixin, ExecMixin):
    def __init__(self, project, task):
        self._project = project
        self._task = task
        self.garbage = []
        self._state = {"prepare": False,
                       "execute": False,
                       "final": False}

        self._work_dir = os.path.join(config.CORRECTION_WORK_DIR, str(self._project["id"]))
        self._makedirs(self._work_dir, safe=True)
        self._rule = self._project["template"]["judge_rule"] if "judge_rule" in self._project["template"] \
                                                                and self._project["template"]["judge_rule"] \
            else self._project["template"]["slug"]
        self._simple_list_name = "%s-%s-%s.simple" % (self._rule, self._project["city"], self._project["id"])
        self._full_list_name = "%s-%s-%s.full" % (self._rule, self._project["city"], self._project["id"])
        #self.garbage.append(self._work_dir)

    def _write(self, file_name, rows, directory="."):
        with open(os.path.join(directory, file_name), 'w') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE, lineterminator='\n')
            writer.writerows(rows)

    def _generate_simple_list(self):
        list = []
        #list.append(["login"])
        for stud in self._project["students"]:
            list.append([stud["user"]["login"]])
        self._write(self._simple_list_name, list, self._work_dir)
        self.garbage.append(os.path.join(self._work_dir, self._simple_list_name))

    def _generate_full_list(self):
        list = []
        #list.append(["login", "city", "firstname", "lastname"])
        for stud in self._project["students"]:
            list.append([stud["user"]["login"], self._project["city"], stud["user"]["firstname"],
                         stud["user"]["lastname"]])
        self._write(self._full_list_name, list, self._work_dir)
        self.garbage.append(os.path.join(self._work_dir, self._full_list_name))

    def prepare(self):
        self._generate_simple_list()
        self._generate_full_list()
        arch = self._cleanfilename("%s-%s" % (self._project["title"], self._project["city"]))
        archive_name = os.path.join(config.ARCHIVE_DIR, arch)
        archive_name = self._last_version("%s.zip" % (archive_name), with_extension=True)
        base_arch = os.path.basename(archive_name)
        print("archive_name: %s" % (base_arch))
        # find latest tarball
        judge = self._project["template"]["judge_uri"]
        if not judge:
            raise Exception("No judge defined")
        res = self._safe_remote_exec(judge, "uname -a")
        if res.return_code != 0:
            raise Exception("Unable to connect to remote judge")
        self._safe_remote_exec(judge, "rm -rf tmp/%s; mkdir -p tmp/%s" % (self._project["id"], self._project["id"]))
        #self._safe_remote_exec(judge, "echo %s; mkdir -p tmp/%s" % (self._project["id"], self._project["id"]))
        self._safe_exec("scp '%s' %s:~/logins/" % (self._simple_list_name, judge), cwd=self._work_dir)
        self._safe_exec("scp '%s' %s:~/logins/" % (self._full_list_name, judge), cwd=self._work_dir)
        self._safe_exec("scp '%s' %s:~/tmp/%s" % (archive_name, judge, self._project["id"]),
                        cwd=self._work_dir, timeout=120)
        res = self._safe_remote_exec(judge, "unzip '%s'" % (base_arch.replace(' ', '\\ ')), cwd="~/tmp/%s" % self._project["id"], timeout=120)
        self._safe_remote_exec(judge, "rm -f '%s'" % (base_arch.replace(' ', '\\ ')), cwd="~/tmp/%s" % self._project["id"])
        logging.warning("CPoolDriver::unzip %s" % res.outs)
        logging.warning("CPoolDriver::unzip %s" % res.errs)
        if res.return_code != 0:
            raise Exception("unable to extract tarball")
        self._safe_remote_exec(judge, "for i in `ls`; do rm -rf ~/rendus/$i/%s; mkdir -p ~/rendus/$i/; " % (self._project["template"]["repository_name"]) +
                               "mv $i ~/rendus/$i/%s ; done" % (self._project["template"]["repository_name"]),
                               cwd="~/tmp/%s" % self._project["id"])
        if res.return_code != 0:
            raise Exception("unable to move pickups")

    def execute(self):
        judge = self._project["template"]["judge_uri"]
        if not judge:
            raise Exception("No judge defined")
        datas = {"simple_list": self._simple_list_name,
                 "full_list": self._full_list_name,
                 }
        datas.update(self._project["template"])
        datas.update(self._project)
        t = self._task["type"] if self._task and "type" in self._task else "preliminary"
        prelim = self._project["template"]["judge_preliminary_exec"]
        action = self._project["template"]["judge_final_exec"] if t == "auto" or not prelim else prelim
        if not action or len(action) == 0:
            raise Exception("No action to exec")
        action = action % datas
        r = self._safe_remote_exec(judge, action, timeout=180)
        logging.warning("CPoolDriver::execute %s" % r.outs)
        logging.warning("CPoolDriver::execute %s" % r.errs)
        return r.return_code

    def final(self):
        # retrieve note + trace ?

        #if self._stage["execute"] && prelim
        #   force emailing
        #if self._stage["execute"] && final
        #   force emailing & push note
        #   push note
        pass

    def clean_remote(self):
        pass

    def clean(self):
        for f in self.garbage:
            self._rmtree(f, safe=True)
        self._rmtree(self._work_dir, safe=True)
        self.garbage = []

    def on_error(self, when, exception):
        # notify admin & clean
        logging.error("CPoolDriver::%s : %s" % (when, str(exception)))
        self.clean()
        self.clean_remote()



class Judge(object):
    def __init__(self, project, task, driver="CPool"):
        # load driver
        self._driver = CPoolDriver(project, task)

    def _prepare(self):
        self._driver.prepare()

    def _execute(self):
        self._driver.execute()

    def _finally(self):
        self._driver.final()

    def _on_error(self, when, exception):
        self._driver.on_error(when, exception)

    def run(self):
        try:
            self._prepare()
            try:
                self._execute()
            except Exception as e:
                self._on_error("execute", e)
            try:
                self._finally()
            except Exception as e:
                self._on_error("finally", e)
        except Exception as e:
            self._on_error("prepare", e)


def manual(project, task_id=None):
    import config
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    engine = create_engine(config.SQL_DB_URI, echo=True, pool_recycle=3600)
    Session = sessionmaker()
    Session.configure(bind=engine)
    from models import Project, Task
    session = Session()
    obj = session.query(Project).get(project)
    t = session.query(Task).get(task_id) if task_id else None

    j = Judge(obj.serialize, t.serialize if task_id else None)
    j.run()