from smile.common import Experiment, Func
from smile.startup import InputSubject


def do_it():
    1/0

exp = Experiment(local_crashlog=True, cmd_traceback=False)
InputSubject()
Func(do_it)

exp.run()
