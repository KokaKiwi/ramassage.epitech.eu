from celery import Celery
from actions.fetch import Fetch
from actions.pickup import Pickup
from actions.judge import Judge
from actions.inform import InformTriche
from celery.bin.celery import result
from celery.result import AsyncResult
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
from celery import chord
from celery import chain

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
def inform_triche(task_id):
    session = Session()
    try:
        task = session.query(Task).get(task_id)
        if not task:
            raise Exception("This task does not exist.")
        project = task.project.serialize
        return InformTriche(project).result
    except IntegrityError:
        session.rollback()
    finally:
        session.close()
    return False

@app.task
def pickup_task(task_id):
    session = Session()
    try:
        task = session.query(Task).get(task_id)
        if not task:
            raise Exception("This task does not exist.")
        project = task.project.serialize
        #return chord((retrieve_scm.s(task_id, project, u["user"]["login"]) for u in project["students"]),
        #      pickup_complete.s(task_id, project)).apply_async()
        return chord((retrieve_scm.s(task_id, project, u["user"]["login"]) for u in project["students"]),
              pickup_complete.s(task_id, project))()
    except IntegrityError:
            session.rollback()
    finally:
        session.close()


@app.task
def scheduled_launch(task_id, token):
    session = Session()
    try:
        obj = session.query(Task).get(task_id)
        obj.status = "ongoing"
        session.add(obj)
        session.commit()
        chain(fetch.si(token), pickup_task.si(task_id), scheduled_launch_done.si(task_id))()
        return True
    except Exception as e:
        logging.warning(e)
        session.rollback()
    finally:
        session.close()
    return False


@app.task
def scheduled_judge(task_id):
    session = Session()
    try:
        task = session.query(Task).get(task_id)
        if not task:
            raise Exception("This task does not exist.")
        project = task.project.serialize
        stask = task.serialize
        if task.project.template.call_judge:
            logging.warning("Time to call Judge!")
            j = Judge(project, stask)
            j.run()
    except Exception as e:
        logging.warning(e)
    finally:
        session.close()
    return True

@app.task
def scheduled_launch_done(task_id):
    session = Session()
    try:
        obj = session.query(Task).get(task_id)
        obj.status = "succeed"
        session.add(obj)
        session.commit()
    except Exception as e:
        logging.warning(e)
        session.rollback()
    finally:
        session.close()
    return True

@app.task
def scheduled_triche(task_id):
    session = Session()
    #try:
    current_task = session.query(Task).get(task_id)
    todos = session.query(Task).join(Project).filter(Project.template_id==1).order_by(Task.launch_date).filter(Task.status != 'succeed').filter(Task.id != current_task.id).all()
    if current_task.type == 'auto' and len(todos) == 0:
        project = current_task.project.serialize
        return InformTriche(project).result
    #except Exception as e:
    #    logging.warning(e)
    #    session.rollback()
    #finally:
    #    session.close()
    return True

@app.task
def pickup_complete(repos, task_id, project):
    #chain (add.s(4, 4), mul.s(8), mul.s(10))
    # archive, distribute, correction, triche
    p = Pickup(task_id, project)
    p.archive()
    p.distribute()
    p.clean_all()
    scheduled_judge(task_id)
    scheduled_triche(task_id)
    return None


@app.task
def retrieve_scm(task_id, project, user):
    begin = datetime.now()
    p = Pickup(task_id, project)
    succeed, repo = p.one(user)
    session = Session()
    try:
        obj = session.query(Project_Student).join(User).filter(Project_Student.project_id==project["id"]).filter(User.login==user).first()
        obj.status = "Succeed" if succeed else "Failed"
        obj.logs = repo._messages
        obj.begin_date = begin
        obj.end_date = datetime.now()

        session.add(obj)
        session.commit()
    except Exception as e:
        logging.warning(e)
        session.rollback()
    finally:
        session.close()
    return succeed



@app.task()
def fetch_onerror(uuid, token, retry):
    print('Task %s raised exception' % uuid)
    if retry < 2:
        print("Retry fetch(%s): #%s" % (token, retry))
        fetch.apply_async(args=[token], link_error=fetch_onerror.s(token, retry + 1),
                          countdown=120)
    # relaunch T.apply_async(countdown=60

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
        need_new = True
        for task in t.tasks:
            if task.type == "auto":
                need_new = False
            if task.type == "auto" and task.status != "ongoing":
                task.launch_date = t.deadline
                session.add(task)
        if need_new:
            session.add(Task(type="auto", launch_date=t.deadline, project=t))
        session.commit()
        return t.serialize
    except IntegrityError as e:
        session.rollback()
    except Exception as e:
        session.rollback()
        logging.error(str(e))
    finally:
        session.close()
    return False
