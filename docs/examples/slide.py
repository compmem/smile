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
Wait(.25)

# Put up a circle and then slide it
circ = Ellipse(color=(jitter(0, 1),
                      jitter(0, 1),
                      jitter(0, 1)))
with UntilDone():
    Wait(until=circ.appeared)
    with Loop(5):
        # slide to new loc and color
        exp.new_col = (jitter(0, 1),
                       jitter(0, 1),
                       jitter(0, 1))
        exp.new_loc = (jitter(0, exp.screen.width),
                       jitter(0, exp.screen.height))
        cu = circ.slide(duration=1.5,
                        color=exp.new_col,
                        center=exp.new_loc)

Wait(.25)

if __name__ == '__main__':
    exp.run()
