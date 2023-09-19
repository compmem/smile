#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from smile.common import *

# set up an experiment
exp = Experiment(show_splash=False)

Wait(0.5)

# use a grid to include a bunch of buttons
with GridLayout(rows=10, left=exp.screen.left, top=exp.screen.height):
    with ButtonPress() as bp:
        MouseCursor()
        for i in range(200):
            Button(name=str(i), text=str(i))

# report which was pressed
Debug(pressed=bp.pressed)

Wait(0.5)

if __name__ == '__main__':
    exp.run()
