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

# show above and below center
Wait(10.)
with Meanwhile():
    with Parallel() as p:
        MouseCursor()
        with Loop() as l:
            mp = MousePress()
            with p.insert():
                Ellipse(center=mp.pos, color=(jitter(0, 1),
                                              jitter(0, 1),
                                              jitter(0, 1)))

Wait(1.0)

if __name__ == '__main__':
    exp.run()
