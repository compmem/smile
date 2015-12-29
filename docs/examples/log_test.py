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

# initial wait
Wait(1.0)

# Wait for a bunch of different times
trials = [{'val':str(i), 'val2':str(i+1)} for i in range(5)]
with Loop(trials) as trial:
    s = Label(text=trial.current['val'], duration=.5)
    l = Log(trial.current,
            appear_time=s.appear_time)
Wait(1.0)

if __name__ == '__main__':
    exp.run()

    #print l.log_filename
    #print s.log_filename
    #from smile.log import LogReader
    
    #lr = LogReader(l.log_filename)
    #print lr.field_names
    #print 
    
