# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile.common import *

# create an experiment
exp = Experiment()

# set up my list
trials = [str(i) for i in range(5)]
GOOD_RT = .5
RESP_KEYS = ['J', 'K']

Wait(1.0)

with Loop(trials) as trial:
    t = Label(text=trial.current, font_size=24)
    with UntilDone():
        # Ensure `t.appear_time` is available by waiting until it exists
        Wait(until=t.appear_time)
        key = KeyPress(keys=RESP_KEYS,
                       base_time=t.appear_time['time'])

    # set whether it was a good RT
    exp.good = key.rt < GOOD_RT
    with If(exp.good):
        Label(text='Awesome!', font_size=30, duration=1.0)
    with Else():
        Label(text='Bummer!', font_size=30, duration=1.0)

    Log(stim_txt=trial.current,
        stim_on=t.appear_time,
        resp=key.pressed,
        rt=key.rt,
        good=exp.good,
        trial_num=trial.i)

    Wait(1.0)

Wait(1.0)


if __name__ == '__main__':
    exp.run()
