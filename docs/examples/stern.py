#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# global imports
import random
import string
import os
import cPickle as pickle

# load all the states
from smile import *

# create an experiment
exp = Experiment()

# config vars
NUM_TRIALS = 2
NUM_ITEMS = [2,3,4]
ITEMS = string.ascii_lowercase
STUDY_DURATION = 1.2
STUDY_ISI = .4
RETENTION_INTERVAL = 1.0
RESP_KEYS = ['J','K']
RESP_DELAY = .2
ORIENT_DURATION = 1.0
ORIENT_ISI = .5
ITI = 1.0

# generate sternberg trial
def stern_trial(nitems=2, lure_trial=False,):

    if lure_trial:
        condition = 'lure'
        items = random.sample(ITEMS,nitems+1)
    else:
        condition = 'target'
        items = random.sample(ITEMS,nitems)
        # append a test item
        items.append(random.sample(items,1)[0])
            
    trial = {'nitems':nitems,
             'study_items':items[:-1],
             'test_item':items[-1],
             'condition':condition,
             }

    return trial

# load or generate trials
trial_file = os.path.join(exp.subj_dir,'trials.pickle')
if os.path.exists(trial_file):
    trials = pickle.load(open(trial_file,'rb'))
else:
    trials = []
    for i in NUM_ITEMS:
        # add target trials
        trials.extend([stern_trial(i,lure_trial=False) for t in range(NUM_TRIALS)])
        # add lure trials
        trials.extend([stern_trial(i,lure_trial=True) for t in range(NUM_TRIALS)])

    # shuffle and number
    random.shuffle(trials)
    for t in range(len(trials)):
        trials[t]['trial_num'] = t

    # save to file
    pickle.dump(trials, open(trial_file,'wb'), 2)

print trials

# define stern trial
# loop over study block
with Loop(trials) as trial:
    # orient stim
    ss_orient = Show(Text('+', 
                          x=Ref(exp['window'],'width')//2, 
                          y=Ref(exp['window'],'height')//2),
                          duration=ORIENT_DURATION)
    Wait(ORIENT_ISI)
    
    # loop over study items
    Set('study_times',[])
    with Loop(trial.current['study_items']) as item:
        # present the letter
        ss = Show(Text(item.current.value, 
                       x=Ref(exp['window'],'width')//2, 
                       y=Ref(exp['window'],'height')//2),
                       duration=STUDY_DURATION)
    
        # wait some jittered amount
        Wait(STUDY_ISI)

        # append the time
        Set('study_times',Get('study_times').append(ss['show_time']))

    # Retention interval
    Wait(RETENTION_INTERVAL - STUDY_ISI)
    
    # present test item
    with Parallel():
        # present the letter
        test_stim = Text(trial.current['test_item'], 
                         x=Ref(exp['window'],'width')//2, 
                         y=Ref(exp['window'],'height')//2,
                         bold=True)
        with Serial():
            # wait some before accepting input
            Wait(RESP_DELAY)
            ks = KeyPress(keys=RESP_KEYS,
                          base_time=test_stim['last_flip']['time'])
            Unshow(test_stim)
            # give feedback

    # Log the trial
    Log(trial_num=trial.current['trial_num'],
        condition=trial.current['condition'],
        resp=ks['pressed'],
        rt=ks['rt'],
        orient_time=ss_orient['show_time'],
        study_items=trial.current['study_items'],
        study_times=Get('study_times'),
        test_item=trial.current['test_item'],
        test_time=test_stim['last_flip'],
        correct=(((trial.current['condition']=='target')&
                 (ks['pressed']==RESP_KEYS[0])) | 
                 ((trial.current['condition']=='lure')&
                 (ks['pressed']==RESP_KEYS[1]))))
    
    Wait(ITI)
    
# run that exp!
exp.run()
