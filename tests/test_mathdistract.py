from smile.common import *
from smile.mathdistract import MathDistract




exp = Experiment()

Wait(1.0)
MathDistract()
Label(text="You are done!", duration=2.0)

exp.run()