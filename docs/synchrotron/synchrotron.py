import sys, os
from loader import Conf

sys.path.insert(0, os.path.realpath("../.."))

from models import Template
from config import SQL_DB_URI

UPDATE_DIFFS = True
INSERT_NEW = True

def main():
    if len(sys.argv) != 2:
        sys.stderr.write("USAGE: %s file.ini\n" % (sys.argv[0]))
        return 1
    c = Conf(sys.argv[1])
    datas = c.getAll()
    if len(datas) == 0:
        sys.stderr.write("Wrong ini file\n")
        return 1

    from sqlalchemy import create_engine
    engine = create_engine(SQL_DB_URI, echo=False)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    templates = session.query(Template).all()
    #print(templates)


    # Templates avec repository_name vide
    # slugs inconnus
    # differences entre .ini et sql

    print("Templates not yet configured:")
    for template in templates:
        if not template.repository_name:
            print(" - %s" % (template))
            if template.slug in datas:
                print("   >> %s" % (datas[template.slug]))
                if INSERT_NEW:
                    template.repository_name = datas[template.slug]["path"]
                    session.add(template)
            else:
                print("   >> Unknown.")

    #for template in templates:
    #

    for slug, d in datas.items():
        matches = [ obj for obj in templates if obj.slug == slug]
        if len(matches) > 1:
            print("[%s] match multiple times: %s" % (slug, matches))
        elif len(matches) == 1 and "path" in d and matches[0].repository_name != d["path"]:
            print("[%s] repository_name differs with the database : ini_file(%s), db(%s)" % (slug, d["path"], matches[0].repository_name))
            if UPDATE_DIFFS:
                m = matches[0]
                m.repository_name = d["path"]
                print("=> Update it.")
                session.add(m)
        elif len(matches) == 0 and False:
            print("[%s] doesn't exist in database. (%s)" % (slug, d))

    session.commit()

if __name__ == "__main__":
    main()
