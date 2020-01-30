from smile.experiment import Experiment
from smile.state import Wait, Debug
from smile.video import Label
from smile.freekey import FreeKey

exp = Experiment()

Wait(.5)

fk = FreeKey(Label(text='XXXXXX', font_size=40), max_resp=1)
Debug(responses=fk.responses)

Label(text='Done', font_size=32, duration=2.0)

fk2 = FreeKey(Label(text='??????', font_size=30))
Debug(responses=fk2.responses)

Wait(1.0)

exp.run()
