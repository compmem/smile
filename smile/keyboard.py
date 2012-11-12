#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from pyglet.window import key

from state import State
from ref import Ref, val

# get the last instance of the experiment class
from experiment import Experiment, now

class KeyPress(State):
    def __init__(self, keys=None, correct_resp=None, base_time=None,
                 duration=-1, parent=None, reset_clock=False):
        # init the parent class
        super(KeyPress, self).__init__(interval=-1, parent=parent, 
                                       duration=-1, reset_clock=reset_clock)

        # save the keys we're watching (None for all)
        self.keys = keys
        self.correct_resp = correct_resp
        self.base_time = base_time  # for calc rt
        self.wait_duration = duration
        
        # if wait duration is -1 wait indefinitely

        # if a wait_duration is specified, that's how long to look for
        # keypresses.

        # this is a variable time state (returns when pressed) so we
        # should tell the parent that the following state should reset
        # its timeline
        self.reset_next = True 

        # get the exp reference
        self.exp = Experiment.last_instance()

        # we're not waiting yet
        self.waiting = False

        # set defaults
        self.pressed = None
        self.press_time = None
        self.correct = False
        self.rt = None

    def _enter(self):
        # process any possible refs in the provided args
        self.keys = val(self.keys)
        if not self.keys is None and not isinstance(self.keys, list):
            # turn into list
            self.keys = [self.keys]
        self.correct_resp = val(self.correct_resp)
        if not self.correct_resp is None and \
          not isinstance(self.correct_resp, list):
            # turn into list
            self.correct_resp = [self.correct_resp]

        self.base_time = val(self.base_time)
        if self.base_time is None:
            # set it to the state time
            self.base_time = self.state_time
        pass

    def _key_callback(self, symbol, modifiers, event_time):
        # check the key and time (if this is needed)
        if self.keys is None or symbol in self.keys:
            # it's all good!, so save it
            self.pressed = key.symbol_string(symbol)
            self.press_time = event_time
            # calc RT if something pressed
            self.rt = event_time['time']-self.base_time

            if not (self.keys is None or self.correct_resp is None):
                # process if it's correct
                if symbol in self.correct_resp:
                    self.correct = True

            # let's leave b/c we're all done
            self.interval = 0
            self.leave()
            
    def _callback(self, dt):
        if not self.waiting:
            self.exp.window.key_callbacks.append(self._key_callback)
            self.waiting = True
        if self.wait_duration > 0 and now() >= self.state_time+self.wait_duration:
            # we're done
            self.interval = 0
            
    def _leave(self):
        # remove the keyboard callback
        self.exp.window.key_callbacks.remove(self._key_callback)
        self.waiting = False
        pass
    


if __name__ == '__main__':

    from experiment import Experiment
    from state import Wait, Func, Loop

    def print_dt(state, *args):
        print args, state.dt

    exp = Experiment()
    
    Func(print_dt, args=['Key Press Test'])

    #kp = KeyPress(keys=[key.J,key.K], correct_resp=key.K)
    #with Loop(cond=kp['pressed']!='K'):
    
    kp = KeyPress(keys=[key.J,key.K], correct_resp=key.K)
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = KeyPress()
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = KeyPress(duration=2.0)
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0, stay_active=True)

    exp.run()
    
