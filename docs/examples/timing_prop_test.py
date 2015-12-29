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
exp = Experiment(background_color='black')

# set the dur and isi for each trial
trials = [{'dur': d, 'isi': i} 
          for d, i in zip([.005, .010, .020, .050, .100, .200, .500, 1.0],
                          [.005, .010, .020, .050, .100, .200, .500, 1.0])]

# add in a bunch of fast switches
trials = [{'dur': .005, 'isi': .005}] * 10 + trials

# double length, reverse, and repeat
trials = trials*2
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)

rect = Rectangle(color=(0, 0, 0, 1.0),
                 size=(exp.screen.width*.9,
                       exp.screen.height*.9))
with UntilDone():
    Wait(1.0)
    with Loop(trials) as trial:
        # wait the isi
        reset = Wait(trial.current['isi'])

        # turn it on
        rect.color = (1,1,1,1) #'white'
        uw = UpdateWidget(rect, color=(1,1,1,1))

        #Wait(until=uw.appear_time)
        #Debug(on_time = uw.appear_time)
        
        #Wait(until=bg.on_screen)

        # reset clock to ensure flip-level timing
        #ResetClock(bg.appear_time['time']-exp.flip_interval/4.)
        #ResetClock(rect.appear_time['time']-.004)

        # wait the dur
        Wait(trial.current['dur'])

        rect.color = (0,0,0,1) #'black'

        # log the on and off times
        #Done(rect)
        Log(on=rect.appear_time,
            #off=rect.disappear_time,
            dur=trial.current['dur'],
            isi=trial.current['isi'])

Wait(1.0)

if __name__ == '__main__':
    exp.run()
