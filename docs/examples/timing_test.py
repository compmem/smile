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
import random

# create an experiment
exp = Experiment(screen_ind=0, pyglet_vsync=True)


# set the dur and isi for each trial
trials = [{'dur':d,'isi':i} 
          for d,i in zip([.005,.010,.020,.050,.100,.200,.500,1.0],
                         [.005,.010,.020,.050,.100,.200,.500,1.0])]

# add in a bunch of fast switches
trials = [{'dur':.005,'isi':.005}]*10 + trials

# double length and repeat
trials = trials*4
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)

# set initially to black
BackColor(color=(0,0,0,1.0))

# # show some txt and images
# txt = Text('Jubba')
# Wait(1.0)
# # make the switch at same time
# with Parallel():
#     Unshow(txt)
#     img = Image('face-smile.png')
# Wait(.5)
# Unshow(img)

Wait(1.0)
with Loop(trials) as trial:
    # wait the isi
    reset = Wait(trial.current['isi'], reset_clock=True)

    # turn it on
    onstim = BackColor(color=(1,1,1,1.0))

    # wait the dur
    Wait(trial.current['dur'])

    # turn if off
    offstim = BackColor(color=(0,0,0,1.0))

    # log the on and off times
    Log(reset=reset['start_time'],
        on=onstim['last_flip'],
        on_start=onstim['start_time'],
        off=offstim['last_flip'],
        off_start=offstim['start_time'],
        dur=trial.current['dur'],
        isi=trial.current['isi'])

Wait(1.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
