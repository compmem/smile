from smile.common import *
from listpresent import ListPresent
import random

WORDS_TO_DISPLAY = ['The', 'Boredom', 'Is', 'The', 'Reason', 'I', 'started', 'Swimming', 'Its', 'Also', 'The', 'Reason', 'I','Started', 'Sinking','Questions','Dodge','Dip','Around','Breath','Hold']
INTER_STIM_DUR = .5
STIM_DUR = 1
INTER_ORIENT_DUR = .2
ORIENT_DUR = 1
random.shuffle(WORDS_TO_DISPLAY)
exp = Experiment()

lp = ListPresent(listOfWords=WORDS_TO_DISPLAY, interStimDur=INTER_STIM_DUR, onStimDur=STIM_DUR, fixDur=ORIENT_DUR, interOrientDur=INTER_ORIENT_DUR)
Log(name='LISTPRESENTLOG',
    timing=lp.timing)
exp.run()
