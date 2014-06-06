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
          for d,i in zip([.005,.010,.020,.040,.080,.160,.320,.640],
                         [.005,.010,.020,.040,.080,.160,.320,.640])]

trials = trials*2
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)

BackColor(color=(0,0,0,1.0))
Wait(2.0, reset_clock=True)
with Loop(trials) as trial:
    #Wait(.005)
    # turn it on
    onstim = BackColor(color=(1,1,1,1.0), reset_clock=True)
    # wait the dur
    Wait(trial.current['dur'])
    # turn if off
    offstim = BackColor(color=(0,0,0,1.0))
    # wait the isi
    Wait(trial.current['isi'])

    # log the on and off times
    Log(on=onstim['last_flip'],
        off=offstim['last_flip'],
        dur=trial.current['dur'],
        isi=trial.current['isi'])

Wait(2.0, stay_active=True)

exp.run()
