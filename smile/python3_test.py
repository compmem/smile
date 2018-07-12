from common import *

exp = Experiment(background_color="GRAY")

label=Label(text="Hello World", duration=1.0)
with Meanwhile():
    Wait(until=label.appear_time, name=Ref(str. 15.001))
    kp = KeyPress(keys='K', base_time=label.appear_time['time'])
Log(name=kp.correct,
    correct=kp.correct)
'''with Loop(lst) as trial:
    label=Label(text=str(trial.current), duration=1.0)
    with Meanwhile():
        kp=KeyPress(keys='K', base_time=label.appear_time['time'], correct_resp='K')
        Debug(x=label.appear_time)
        Debug(y=label.appear_time['time'])'''


exp.run()

'''
Wait(interStimulusTime)
with Loop(block1) as trial:
    with Loop(trial.current) as trial2:
        b1stim = Label(text=trial2.current["text"], font_size=font2, duration=maxResponseTime)
        with Meanwhile():
            Wait(until=b1stim.appear_time)
            #@FIX: receiving ref.NotAvailableError on line 29
            Debug(x="WORLDY")
            #Debug(y=type(b1stim.appear_time))
            Debug(x=b1stim.appear_time)
            Debug(x=b1stim)
            kp=KeyPress(keys='J', base_time=1)#b1stim.appear_time['time'])
            #kp=KeyPress(keys=keyDict, base_time=b1stim.appear_time['time'], correct_resp=trial2.current["correct_resp"])
        Log(trial2.current,
            name="block1",
            pressed=kp.pressed,
            correct=kp.correct,
            rt=kp.rt,
            base_time=kp.base_time,
            appear_time=b1stim.appear_time)
'''