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

# initial wait
Wait(1.0)

# Present two stim with embedded If
with Loop(range(10)) as trial:
    with Parallel():
        with If((trial.current % 2) == 0):
            Label(text='      X', duration=2.0)
        with Else():
            Label(text='O      ', duration=2.0)
        with Serial():
            Label(text='   :   ', duration=1.0)
            Label(text='   !   ', duration=1.0)

Wait(1.0)

if __name__ == '__main__':
    exp.run()
