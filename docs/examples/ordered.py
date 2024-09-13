#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

Wait(1.0)

# Create stims
with Parallel():
    stimB = Label(text="B", x=exp.screen.center_x + 25,
                  font_size=64,
                  color='blue')
    stimF = Label(text="F", x=exp.screen.center_x - 25,
                  font_size=64,
                  color='orange')

# Do the above state until the below states leave
with UntilDone():
    Wait(1.0)
    with Parallel():
        stimB.slide(x=exp.screen.center_x - 25, duration=3.0)
        stimF.slide(x=exp.screen.center_x + 25, duration=3.0)

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
