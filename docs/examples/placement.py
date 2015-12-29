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
Wait(2.)
with Meanwhile():
    with Parallel():
        a = Label(text='Above', center_bottom=exp.screen.center)
        b = Label(text='Below', center_top=exp.screen.center)
        c = Label(text='Way Below', center_top=(b.center_x, b.bottom-100))

Wait(1.0)

if __name__ == '__main__':
    exp.run()
