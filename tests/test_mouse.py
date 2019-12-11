
from smile.experiment import Experiment
from smile.state import Wait, Debug, Loop, Meanwhile, Record, Log, Parallel

from smile.mouse import MouseRecord, MouseCursor, MousePress, MousePos, MouseWithin
from smile.video import Label, Button, ButtonPress
def print_dt(state, *args):
    print(args)

exp = Experiment(show_splash=True)

with Meanwhile():
    #Record(pos=MousePos(), button=MouseButton())
    with Parallel():
        MouseRecord()
        MouseCursor()

Wait(2.0)
MouseCursor("smile/face-smile.png", (125, 125), duration=5.0)

with Parallel():
    lbl1 = Label(text="Click me dogggggggg", blocking=False)
    with Loop(10):
        Debug(mw=MouseWithin(lbl1))
        Wait(1.0)

Debug(name='Mouse Press Test')

exp.last_pressed = ''
with Loop(conditional=(exp.last_pressed!='RIGHT')):
    kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    exp.last_pressed = kp.pressed
    Log(pressed=kp.pressed, rt=kp.rt)

kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
Wait(1.0)

kp = MousePress()
Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
Wait(1.0)

kp = MousePress(duration=2.0)
Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
Wait(1.0)

exp.run()
