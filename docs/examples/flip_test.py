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

# define the trials for the experiment
trials = [{'txt':str(i)} for i in range(50)]

Set('stim',False)
Set('stim_shown',False)
Wait(1.0)
with Loop(trials) as trial:
    Wait(.005)
    with If(Get('stim'), save_log=False) as if_state:
        with if_state.true_state:
            with Parallel():
                ustim = Update(Get('stim'),'text',trial.current['txt'])
                # ustim2 = Update(Get('stim'),'x',
                #                 Ref(gfunc=lambda : random.uniform(300,500)))
                ustim2 = Update(Get('stim'),'x',
                                Get('stim_shown').x+5)
                ustim3 = Update(Get('stim'),'font_size',
                                Get('stim_shown').font_size+1.0)
            Set('stim_flip',ustim['last_flip'])
        with if_state.false_state:
            stim = Text(trial.current['txt'], 
                        x=300, 
                        #x=exp.window.width//2, 
                        y=Ref(exp['window'],'height')//2,
                        bold=True)
            Set('stim', stim, save_log=False)
            Set('stim_shown', stim['shown'], save_log=False)
            Set('stim_flip',stim['last_flip'])

    Log(txt=trial.current['txt'],
        flip=Get('stim_flip'))

Unshow(stim)
Wait(2.0)
Show(Text('Done!!!', 
          x=Ref(exp['window'],'width')//2, 
          y=Ref(exp['window'],'height')//2,),
          duration=2.0)
Wait(2.0, stay_active=True)

exp.run()
