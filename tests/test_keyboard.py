from smile.experiment import Experiment
from smile.state import Wait, Debug, Loop, UntilDone, Log, Meanwhile
from smile.keyboard import Key, KeyRecord, KeyPress


exp = Experiment()

with Meanwhile():
    KeyRecord(name="record_all_key_presses")

Debug(name='Press T+G+D or SHIFT+Q+R')
Wait(until=((Key("T") & Key("G") & Key("D")) |
            (Key("SHIFT") & Key("Q") & Key("R"))))
Debug(name='Key Press Test')

exp.last_pressed = ''

with Loop(conditional=(exp.last_pressed != 'K')):
    kp = KeyPress(keys=['J', 'K'], correct_resp='K')
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    exp.last_pressed = kp.pressed
    Log(pressed=kp.pressed, rt=kp.rt)

KeyRecord()
with UntilDone():
    kp = KeyPress(keys=['J', 'K'], correct_resp='K')
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

    kp = KeyPress()
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

    kp = KeyPress(duration=2.0)
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

exp.run()
