
from smile.experiment import Experiment
from smile.state import Debug, Wait, Log, Loop
from smile.pulse import Pulse

# set up default experiment
exp = Experiment()

with Loop(15):
    pulse = Pulse(code='S1')
    Wait(duration=1.0, jitter=1.0)
    Log(name='pulse',
        pulse_on=pulse.pulse_on,
        pulse_code=pulse.code,
        pulse_off=pulse.pulse_off)

# print something
Debug(width=exp.screen.width, height=exp.screen.height)

# run the exp
exp.run(trace=False)
