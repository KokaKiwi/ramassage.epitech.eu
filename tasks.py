from celery import Celery
from actions.fetch import Fetch
from celery.bin.celery import result
from sqlalchemy import create_engine
import config
from models import Project
from models import User
from models import Task
from models import Project_Student
from models import Template
import logging
from sqlalchemy.exc import IntegrityError
import json
from datetime import datetime

app = Celery('tasks')
app.config_from_object("workerconfig")

engine = create_engine(config.SQL_DB_URI, echo=True, pool_recycle=3600)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
Session.configure(bind=engine)

@app.task
def add(x, y):
        return x + y

@app.task
def fetch(token):
    session = Session()
    try:
        obj = Fetch(token)
        print(obj.result)

        t = session.query(Project).filter_by(token=token).first()
        print(t)
        datas = obj.result
        if not t:
            logging.info("Create new project")
            tpl = session.query(Template).filter_by(codemodule=datas["module_code"], slug=datas["slug"]).first()
            if not tpl:
                logging.info("Create new Template")
                tpl = Template(codemodule=datas["module_code"], slug=datas["slug"])
                # repository_name, call*, school, ...
                session.add(tpl)
            t = Project(template=tpl)
            session.add(t)

        t.token = datas["token"]
        t.scolaryear = datas["scolaryear"]
        t.module_title = datas["module_title"]
        t.module_code = datas["module_code"]
        t.instance_code = datas["instance_code"]
        t.location = datas["location"]
        t.title = datas["title"]
        t.deadline = datetime.strptime(datas["deadline"], "%Y-%m-%d %H:%M:%S")
        t.promo = datas["promo"]
        t.groups = json.dumps(datas["groups"])
        t.last_update = datetime.now()
        resp = []
        for user in datas["resp"]:
            u = session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                session.add(u)
            resp.append(u)
        t.resp = resp
        template_resp = []
        for user in datas["template_resp"]:
            u = session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                session.add(u)
            template_resp.append(u)
        t.template_resp = template_resp
        assistants = []
        for user in datas["assistants"]:
            u = session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                session.add(u)
            assistants.append(u)
        t.assistants = assistants
        t.students = []
        for user in datas["students"]:
            u = session.query(User).filter_by(login=user["login"]).first()
            if not u:
                u = User(firstname=user["firstname"], lastname=user["lastname"], login=user["login"])
                session.add(u)
            t.students.append(Project_Student(user=u, project=t))

        session.add(t)
        rescheduled = False
        for task in t.tasks:
            if task.type == "auto":
                task.launch_date = t.deadline
                session.add(task)
                rescheduled = True
        if not rescheduled:
            session.add(Task(type="auto", launch_date=t.deadline, project=t))
        session.commit()
        return t.serialize
    except IntegrityError as e:
        session.rollback()
    #except Exception as e:
    #    session.rollback()
    #    logging.error(str(e))
    finally:
        session.close()
    return False
