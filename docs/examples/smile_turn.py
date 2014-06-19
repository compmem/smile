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
exp = Experiment(screen_ind=0, pyglet_vsync=True)

# set initially to white
BackColor(color=(1,1,1,1.0))

Wait(1.0)

# fade in
nsteps = 254
img = Image('face-smile.png',rotation=-nsteps,opacity=0)
steps = [i/float(nsteps) for i in range(nsteps,-1,-1)]
with Loop(steps) as step:
    with Parallel():
        BackColor(color=[step.current]*3 + [1.0])
        Update(img,'rotation',img['shown'].rotation+1)
        Update(img,'opacity',img['shown'].opacity+1)
    ResetClock()
    Wait(.02)

Wait(2.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
