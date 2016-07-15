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

Wait(1.0)

BackgroundColor(color='red', duration=1.0)
BackgroundColor(color='orange', duration=1.0)
BackgroundColor(color='yellow', duration=1.0)
BackgroundColor(color='green', duration=1.0)
BackgroundColor(color='blue', duration=1.0)
BackgroundColor(color='purple', duration=1.0)

Wait(1.0)

if __name__ == '__main__':
    exp.run()
