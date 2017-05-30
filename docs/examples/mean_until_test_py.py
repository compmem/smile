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
exp = Experiment()

# Parallel equivalent to Meanwhile
with Loop(3):
    with Parallel():
        lblp = Label(text="This is on the screen for exactly 2 seconds",
                     duration=2., blocking=True)
        with Serial(blocking=False):
            Wait(until=lblp.appear_time)
            Label(text='This is on the screen for exactly 1 second',
                  top=lblp.bottom-20, duration=1.)
    Wait(1.)

# Meanwhile approach
with Loop(3):
    lblmw = Label(text="This is on the screen for exactly 2 seconds",
                  duration=2.)
    with Meanwhile():
        Wait(until=lblmw.appear_time)
        Label(text='This is on the screen for exactly 1 second',
              top=lblmw.bottom-20, duration=1.)
    Wait(1.)

# UntilDone
with Loop(3):
    lblut = Label(text="This should be on the screen for exactly 1 second",
                  duration=2.)
    with UntilDone():
        Wait(until=lblut.appear_time)
        Label(text='This is on the screen for exactly 1 second',
              top=lblut.bottom-20, duration=1.)
    Wait(1.)


if __name__ == '__main__':
    exp.run()

