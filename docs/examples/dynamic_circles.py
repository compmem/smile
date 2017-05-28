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

# placeholder for saving inserted circs
exp.circs = []

# Accept input for 5 seconds
Wait(5.)
with Meanwhile():
    # put it all in a parallel so we can keep adding stuff
    with Parallel() as p:
        # show the cursor
        MouseCursor()
        with Loop() as l:
            # wait for a mouse press
            mp = MousePress()
            with p.insert() as ins:
                # add a circle with random color
                circ = Ellipse(center=mp.pos, color=(jitter(0, 1),
                                                     jitter(0, 1),
                                                     jitter(0, 1)))
            exp.circs = exp.circs + [ins.first]

# print out the locs we saved
with Loop(exp.circs, save_log=False) as c:
    Debug(i=c.i,
          center=c.current.center,
          color=c.current.color)
Wait(1.0)

if __name__ == '__main__':
    exp.run()
