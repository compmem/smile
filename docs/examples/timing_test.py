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
exp = Experiment(screen_ind=0, pyglet_vsync=False)

# set the dur and isi for each trial
trials = [{'dur':d,'isi':i} 
          for d,i in zip([.005,.010,.020,.050,.100,.200,.500,1.0],
                         [.005,.010,.020,.050,.100,.200,.500,1.0])]

# add in a bunch of fast switches
trials = [{'dur':.005,'isi':.005}]*10 + trials

# double length, reverse, and repeat
trials = trials*2
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)

# set initially to black
BackColor(color=(0,0,0,1.0))

Wait(1.0)
with Loop(trials) as trial:
    # wait the isi
    reset = Wait(trial.current['isi'])

    # turn it on
    onstim = BackColor(color=(1,1,1,1.0))
    
    # reset clock to ensure flip-level timing
    ResetClock(onstim['last_flip']['time']-exp['flip_interval']/4.)

    # wait the dur
    Wait(trial.current['dur'])

    # turn if off
    offstim = BackColor(color=(0,0,0,1.0))

    # log the on and off times
    Log(reset=reset['start_time'],
        on=onstim['last_flip'],
        on_start=onstim['start_time'],
        on_draw=onstim['last_draw'],
        on_update=onstim['last_update'],
        off=offstim['last_flip'],
        off_start=offstim['start_time'],
        off_draw=offstim['last_draw'],
        off_update=offstim['last_update'],
        dur=trial.current['dur'],
        isi=trial.current['isi'])

Wait(1.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
