import io
import csv
from .execution import ExecMixin

class ClocMixin(ExecMixin):
    """
        Needs 'cloc' binary
    """
    def __init__(self):
        pass

    def _transform(self, cols, rows, key):
        result = {}
        for row in rows:
            obj = {}
            i = 0
            for k in cols:
                if len(row[i]) > 0:
                    obj[k] = row[i]
                i += 1
            result[obj[key]] = obj
        return result

    def _launch_cloc(self, dirname):
        out = self._safe_exec(["cloc", "--csv", "--csv-delimiter=';'", "--quiet", dirname], timeout=20)
        if out.return_code != 0:
            raise Exception("Unable to retrieve cloc data")
        f = io.StringIO(out.outs.decode("utf-8").replace("'", ""))
        rows = []
        next(f)
        reader = csv.reader(f, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"')
        for row in reader:
            rows.append(row)
        obj = self._transform(rows[0][:-1], rows[1:], "language")
        #print("rows: " + str(obj))
        return obj
