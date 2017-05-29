#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile.common import *

# create an experiment
exp = Experiment(background_color='black')

exp.err_text = '0.0'
with Loop():
    # flash some text
    text = Label(text=exp.err_text, duration=.005, font_size=48)
    Wait(until=text.disappear_time)
    ResetClock(text.disappear_time['time'])
    Wait(.005)
with UntilDone():
    with Loop(100):
        # accept either a mouse or key press
        with Parallel():
            mp = MousePress(blocking=False)
            kp = KeyPress(blocking=False)
        with If(mp.press_time):
            exp.err_text = Ref(str, mp.press_time['error'])
        with Elif(kp.press_time):
            exp.err_text = Ref(str, kp.press_time['error'])
        with Else():
            Debug(kpt=kp.press_time, mpt=mp.press_time)

Wait(1.0)

if __name__ == '__main__':
    exp.run()
