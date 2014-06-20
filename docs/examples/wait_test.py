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

# Wait for a bunch of different times
times = [.001,.002,.005,.010,.020,.050,.1,.2,.5,1,2,5.]
with Loop(times) as time:
    w = Wait(time.current)
    Log(call_error=w['last_call_error'],
        time=time.current,
        start=w['start_time'],
        call_time=w['last_call_time'])
Wait(1.0, stay_active=True)

if __name__ == '__main__':
    exp.run()
