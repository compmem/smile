#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# Load the common states
from smile.common import *

# create an experiment
exp = Experiment()

# initial wait
Wait(1.0)

# Wait for a bunch of different times
times = [.001,.002,.005,.010,.020,.050] #,.1,.2,.5,1,2,5.]
times_copy = times[:]
times_copy.reverse()
times.extend(times_copy)

with Loop(times) as time:
    w = Wait(time.current)
    db = Debug(cur_time=time.current)
    ResetClock(db.leave_time)

Wait(1.0)

if __name__ == '__main__':
    import cProfile
    cProfile.run('exp.run()','waitstats')
