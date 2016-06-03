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

# Initial wait
Wait(1.0)

# Show a label
Label(text=unichr(10025) + u" Unicode " + u"\u2729",
      font_size=64, font_name='Arial Unicode')
with UntilDone():
    KeyPress()

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
