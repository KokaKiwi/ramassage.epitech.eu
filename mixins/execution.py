__author__ = 'steven'

import subprocess, shlex

class ExecResult(object):
    def __init__(self, return_code, outs, errs, exception=None):
        self.return_code = return_code
        self.outs = outs
        self.errs = errs
        self.exception = exception


class ExecMixin(object):
    def __init__(self):
        pass

    def _safe_exec(self, command, timeout=15):
        if isinstance(command, str):
            command = shlex.split(command)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired as e:
            proc.kill()
            outs, errs = proc.communicate()
            return ExecResult(proc.returncode, outs, errs, e)
        return ExecResult(proc.returncode, outs, errs)

