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

# define the trials for the experiment
trials = [{'txt': str(i)} for i in range(50)]

# save stim
txt = Label(text=trials[0]['txt'],
            x=300,
            y=exp.screen.center_y,
            bold=True)
with UntilDone():
    Wait(1.0)
    with Loop(trials[1:]) as trial:
        Wait(.005)
        uw = UpdateWidget(txt,
                          text=trial.current['txt'],
                          x=txt.x+5,
                          font_size=txt.font_size+1.0)

        Log(name='flip_test',
            txt=trial.current['txt'],
            appear=uw.appear_time)

Wait(2.0)
Label(text='Done!!!', font_size=42, duration=2.0)
Wait(2.0)

if __name__ == '__main__':
    exp.run()
