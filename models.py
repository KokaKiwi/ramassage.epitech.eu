__author__ = 'steven'

# mysql+mysqldb://<user>:<password>@<host>[:<port>]/<dbname>
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Boolean, Enum, DateTime, Text, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from config import SQL_URI, SQL_DB_URI
import sys
import datetime,json


Base = declarative_base()

def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    firstname = Column(String(50), nullable=True)
    lastname = Column(String(50), nullable=True)
    login = Column(String(30), unique=True, nullable=False)

    def __repr__(self):
        return "<User (id='%s', firstname='%s', lastname='%s', login='%s')>" % (self.id,
                                                                                   self.firstname,
                                                                                   self.lastname,
                                                                                   self.login)
    @property
    def serialize(self):
        return {"id": self.id, "firstname": self.firstname, "lastname": self.lastname, "login": self.login}

class Template(Base):
    __tablename__ = 'template'
    id = Column(Integer, primary_key=True)
    codemodule = Column(String(40), nullable=False)
    slug = Column(String(40), nullable=False)
    repository_name = Column(String(90), nullable=True)
    call_moulitriche = Column(Boolean, default=False)
    call_judge = Column(Boolean, default=False)
    judge_uri = Column(String(100), nullable=True)
    judge_rule = Column(String(50), nullable=True)
    judge_preliminary_exec = Column(String(200), nullable=True)
    judge_final_exec = Column(String(200), nullable=True)
    school = Column(Enum("epitech", "coding-academy", "webacademy", "samsung"), default="epitech")
    projects = relationship("Project", backref="template")
    __table_args__ = (UniqueConstraint('codemodule', 'slug', name='_codemodule_slug_uc'),
                     )

project_assistant_user_table = Table('project_assistant_user', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)


project_templateresp_user_table = Table('project_templateresp_user', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

project_resp_user_table = Table('project_resp_user', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

class Project_Student(Base):
    __tablename__ = 'project_student_user'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    status = Column(Enum("Succeed", "Failed", "WithErrors"), nullable=True)
    logs = Column(Text, nullable=True)
    begin_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    user = relationship("User")
    #project = relationship("Project")

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    token = Column(String(40), nullable=False)
    template_id = Column(Integer, ForeignKey('template.id'))
    scolaryear = Column(Integer, nullable=False)
    module_title = Column(String(40), nullable=False)
    module_code = Column(String(40), nullable=False)
    instance_code = Column(String(15), nullable=False)
    location = Column(String(20), nullable=False)
    title = Column(String(50), nullable=False)
    deadline = Column(DateTime, nullable=False)
    promo = Column(Integer, nullable=True)
    groups = Column(Text, nullable=True) # json packed groups
    students = relationship("Project_Student", backref=backref("project"))
    resp = relationship("User",
                    secondary=project_resp_user_table,
                    backref="projects_as_resp")
    template_resp = relationship("User",
                    secondary=project_templateresp_user_table,
                    backref="projects_as_templateresp")
    assistants = relationship("User",
                    secondary=project_assistant_user_table,
                    backref="projects_as_assistant")
    last_update = Column(DateTime, nullable=False)
    last_action = Column(DateTime, nullable=True)
    tasks = relationship("Task", backref=backref("project"))

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    type = Column(Enum("auto", "preliminary", "manual"), default="auto")
    launch_date = Column(DateTime, nullable=False)
    status = Column(Enum("ongoing", "todo", "succeed", "failed"), default="todo")
    project_id = Column(Integer, ForeignKey("project.id"))
    extend = Column(Text, nullable=True) # json packed extended properties


if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine(SQL_DB_URI, echo=True)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker()
    Session.configure(bind=engine)

    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            en = create_engine(SQL_URI, echo=True)
            conn = en.connect()
            conn.execute("commit")
            conn.execute('drop database if exists ramassage')
            conn.execute("create database ramassage")
            conn.close()

            Base.metadata.create_all(engine)
            sys.exit(0)
        if sys.argv[1] == "test_create":
            session = Session()
            ed_user = User(firstname="Steven", lastname="MARTINS", login="martin_6")

            session.add(ed_user)

            template = Template(
                codemodule="B-CUI-150",
                slug="pepito",
                repository_name="pepito",
                call_moulitriche=True,
                call_judge=False,
                school="epitech"
            )

            session.add(template)

            students = [
                User(firstname="Maxime", lastname="D", login="dufres_m"),
                User(firstname="Louis", lastname="K", login="kreher_l"),
                User(firstname="Loïc", lastname="H", login="hidou_l"),
                User(firstname="Jean", lastname="L", login="lemarq_j"),
            ]

            for stud in students:
                session.add(stud)

            resp = [
                ed_user
            ]

            template_resp = [
                User(firstname="Pierre-Jean", lastname="LEGER", login="leger_i")
            ]

            assistants = [
                User(firstname="Victorien", lastname="RAMAGET", login="ramage_v"),
                User(firstname="Nathan", lastname="JANEZCO", login="janecz_n")
            ]

            project = Project(
                token="1f6d77c4-0668-093b-b29e-6a20cb283b4d",
                template=template,
                scolaryear=2014,
                module_title="B2 - Security - beginners",
                module_code="B-CUI-150",
                instance_code="NCY-2-1",
                location="FR/NCY",
                title="Pepito",
                deadline=datetime.datetime.strptime("2015-04-19 23:42:00", "%Y-%m-%d %H:%M:%S"),
                promo=2019,
                groups=json.dumps({}),
                resp=resp,
                template_resp=template_resp,
                last_update=datetime.datetime.now(),
            )
            project.assistants = assistants
            for stud in students:
                project.students.append(Project_Student(user=stud,
                                                        project=project,
                                                        ))

            session.add(ed_user)
            session.add(project)

            session.add(Task(type="auto", launch_date=project.deadline, project=project))
            session.add(Task(type="preliminary", launch_date=project.deadline - datetime.timedelta(days=1), project=project))

            session.commit()
        if sys.argv[1] == "test_update":
            session = Session()
            our_user = session.query(User).filter_by(login='mart_s').first()
            our_user.firstname = "Steven1"
            session.commit()

        if sys.argv[1] == "test_read":
            session = Session()
            #ed_user = Student(firstname="Steven", lastname="MARTINS", login="martin_6")
            #session.add(ed_user)
            our_user = session.query(User).filter_by(firstname='Steven').first()
            #session.commit()

