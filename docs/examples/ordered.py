#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile import *

# create an experiment
exp = Experiment()

Wait(1.0)

# create stims
with Parallel():
    stimB = Label(text="B", x=exp.screen.center_x + 50,
                  font_size=32,
                  color=(0, 1, 1, 1))
    stimF = Label(text="F", x=exp.screen.center_x - 50,
                  font_size=32,
                  color=(1, 1, 0, 1.))
with UntilDone():

    Wait(1.0)
    with Parallel():
        stimB.slide(x=exp.screen.center_x - 50, duration=2.0)
        stimF.slide(x=exp.screen.center_x + 50, duration=2.0)

Wait(1.0)

if __name__ == '__main__':
    exp.run()
