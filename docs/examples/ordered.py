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

# make some ordered groupings
from pyglet.graphics import OrderedGroup

background = OrderedGroup(0)
foreground = OrderedGroup(1)

# create an experiment
exp = Experiment(screen_ind=0, pyglet_vsync=False)

Wait(1.0)

# create stims
stimF = Text("F", x=(exp['window'].width//2)-50, font_size=32, 
             color=(255,255,0,255), group=foreground)
stimB = Text("B", x=(exp['window'].width//2)+50, font_size=32, 
             color=(0,255,255,255), group=background)

Wait(1.0)

# move them
with Loop(range(100)):
    upstate = Update(stimF, "x", stimF['shown'].x+1)
    Update(stimB, "x", stimB['shown'].x-1)
    ResetClock(upstate['last_flip']['time'])
    Wait(.05)
    
Wait(2.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
