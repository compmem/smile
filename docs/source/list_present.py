from smile import *
from smile.state import Subroutine
@Subroutine
def ListPresent(self, listOfWords=[], interStimDur=.5, onStimDur=1, fixDur=1, interOrientDur=.2):
    self.timing = []
    with Loop(listOfWords) as trial:
        fix = Label(text='+', duration=fixDur)
        oriWait = Wait(interOrientDur)
        stim = Label(text=trial.current, duration=onStimDur)
        stimWait = Wait(interStimDur)
        self.timing += [Ref(dict,
                            fix_dur=fix.duration,
                            oriWait_dur=oriWait.duration,
                            stim_dur=stim.duration,
                            stimWait_dur=stimWait.duration)]