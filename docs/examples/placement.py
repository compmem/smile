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
exp = Experiment(screen_ind=0, pyglet_vsync=False)

# initial wait
Wait(1.0)

# show above and below center
with Parallel():
    a = Text('Above',x=exp['window'].width//2,y=exp['window'].height//2,
             anchor_y='bottom') 
    b = Text('Below',x=exp['window'].width//2,y=exp['window'].height//2,
             anchor_y='top')
    c = Text('Way Below', x=b['x'], y=b['y']-100, anchor_y='top')

Wait(2.)

with Parallel():
    Unshow(a)
    Unshow(b)
    Unshow(c)

Wait(2.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
