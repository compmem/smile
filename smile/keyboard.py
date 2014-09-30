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
    def __init__(self, keys=None, correct_resp=None, base_time=None, until=None,
                 duration=-1, parent=None, save_log=True):
        # init the parent class
        super(KeyPress, self).__init__(interval=-1, parent=parent, 
                                       duration=-1,
                                       save_log=save_log)

        # save the keys we're watching (None for all)
        if not isinstance(keys, list):
            keys = [keys]
        self.keys = keys
        if not isinstance(correct_resp, list):
            correct_resp = [correct_resp]
        self.correct_resp = correct_resp
        self.base_time_src = base_time  # for calc rt
        self.base_time = None
        if not isinstance(duration, Ref) and duration == -1:
            self.wait_duration = None
        else:
            self.wait_duration = duration
        self.wait_until = until
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        
        # if wait duration is -1 wait indefinitely

        # if a wait_duration is specified, that's how long to look for
        # keypresses.

        # we're not waiting yet
        self.waiting = False

        # append log vars
        self.log_attrs.extend(['keys', 'correct_resp', 'base_time',
                               'pressed', 'press_time', 
                               'correct', 'rt'])

    def _enter(self):
        # reset defaults
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        self.base_time = None

    def _key_callback(self, symbol, modifiers, event_time):
        # check the key and time (if this is needed)
        keys = val(self.keys)
        correct_resp = val(self.correct_resp)
        sym_str = key.symbol_string(symbol)
        if None in keys or sym_str in keys:
            # it's all good!, so save it
            self.pressed = sym_str
            self.press_time = event_time

            # # fill the base time val
            # self.base_time = val(self.base_time_src)
            # if self.base_time is None:
            #     # set it to the state time
            #     self.base_time = self.state_time
            
            # calc RT if something pressed
            self.rt = event_time['time']-self.base_time

            if self.pressed in correct_resp:
                self.correct = True

            # let's leave b/c we're all done
            #self.interval = 0
            self.leave()
            
    def _callback(self, dt):
        if not self.waiting:
            self.exp.window.key_callbacks.append(self._key_callback)
            self.waiting = True
        if self.base_time is None:
            self.base_time = val(self.base_time_src)
            if self.base_time is None:
                # set it to the state time
                self.base_time = self.state_time
        wait_duration = val(self.wait_duration)
        if (not wait_duration is None) and (now() >= self.base_time+wait_duration):
            self.leave()
        elif val(self.wait_until):
            self.leave()
            
    def _leave(self):
        # remove the keyboard callback
        self.exp.window.key_callbacks.remove(self._key_callback)
        self.waiting = False
        pass
    


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Func, Loop

    def print_dt(state, *args):
        print args, state.dt

    exp = Experiment()
    
    Func(print_dt, args=['Key Press Test'])

    Set('last_pressed','')
    with Loop(conditional=(Get('last_pressed')!='K')):
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Set('last_pressed',kp['pressed'])
        Log(pressed=kp['pressed'], rt=kp['rt'])
    
    kp = KeyPress(keys=['J','K'], correct_resp='K')
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = KeyPress()
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = KeyPress(duration=2.0)
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0, stay_active=True)

    exp.run()
    
