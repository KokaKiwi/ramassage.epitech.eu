__author__ = 'steven'

from sqlalchemy import create_engine
import config
from models import Task
from datetime import datetime
from datetime import timedelta
import logging
import time
from models import dump_datetime

engine = create_engine(config.SQL_DB_URI, echo=True, pool_recycle=3600)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
Session.configure(bind=engine)
from tasks import scheduled_launch

class Scheduler(object):
    def __init__(self):
        pass

    def restore(self, minutes=5):
        session = Session()
        tasks = session.query(Task).filter_by(status="ongoing").filter(Task.launch_date <
                                                                       datetime.now() -
                                                                       timedelta(minutes = minutes)).all()
        for task in tasks:
            logging.warning("RESTORE task <id: %s, launch_date=%s, status=%s>" % (task.id, dump_datetime(task.launch_date, split=False), task.status))
            task.status = "todo"
            session.add(task)
        session.commit()

    def run(self):
        while True:
            session = Session()
            try:
                tasks = session.query(Task).filter_by(status="todo").filter(Task.launch_date < datetime.now()).all()
                for task in tasks:
                    print("task <id: %s, launch_date, status=%s>")
                    task.status = "ongoing"
                    session.add(task)
                    session.commit()
                    scheduled_launch.delay(task.id, task.project.token)

                print(tasks)
            finally:
                session.close()
            time.sleep(10)




if __name__ == "__main__":
    s = Scheduler()
    s.restore()
    s.run()

    #call task
    #  refresh if token
    #  change task state
    #  if succeed => launch task
    #  when it's done => update sql

