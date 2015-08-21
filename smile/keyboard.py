#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import CallbackState
from ref import val
from clock import clock
from experiment import Experiment


def Key(name):
    exp = Experiment.last_instance()
    return exp.app.get_key_ref(name.upper())


class KeyState(CallbackState):
    def on_key_down(self, keycode, text, modifiers, event_time):
        self.claim_exceptions()
        self._on_key_down(keycode, text, modifiers, event_time)

    def _on_key_down(self, keycode, text, modifiers, event_time):
        pass

    def on_key_up(self, keycode, event_time):
        self.claim_exceptions()
        self._on_key_up(keycode, event_time)

    def _on_key_up(self, keycode, event_time):
        pass

    def _callback(self):
        self.exp.app.add_callback("KEY_DOWN", self.on_key_down)
        self.exp.app.add_callback("KEY_UP", self.on_key_up)

    def _leave(self):
        print "Moo!"
        self.exp.app.remove_callback("KEY_DOWN", self.on_key_down)
        self.exp.app.remove_callback("KEY_UP", self.on_key_up)
        super(KeyState, self)._leave()


class KeyPress(KeyState):
    """
    Accept keyboard responses.
    
    Parameters
    ----------
    keys : list of str
        List of keys that will be accepted as a response. Refer to
        module pyglet.window.key documentation for compilation of
        possible key constants. 
    correct_resp : str
        Correct key response for the current trial.
    base_time : int
        Manually set a time reference for the start of the state. This
        will be used to calculate reaction times.
    until : int
        Time provided to make a response.
    duration : {0.0, float}
        Duration of the state in seconds.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    save_log : bool
        If set to 'True,' details about the state will be
        automatically saved in the log files.
        
    Example
    -------
    KeyPress(keys=['J','K'])
    Accept a key press as a response, but limit responses to either
    'J' or 'K'.
    
    Log Parameters
    ---------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters.        
        pressed :
            Which key was pressed.
        press_time:
            Time at which key was pressed.
        correct:
            Boolean indicator of whether the response was correct
            or incorrect.
        rt: 
            Amount of time that has passed between stimulus onset
            and the participant's response. Dependent on base_time.   
    """
    def __init__(self, keys=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None):
        # init the parent class
        super(KeyPress, self).__init__(parent=parent,
                                       duration=duration,
                                       save_log=save_log,
                                       name=name)

        # save the keys we're watching (None for all)
        if not isinstance(keys, list):
            keys = [keys]
        self.keys = keys
        if not isinstance(correct_resp, list):
            correct_resp = [correct_resp]
        self.correct_resp = correct_resp
        self.base_time_src = base_time  # for calc rt
        self.base_time = None
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None

        # append log vars
        self.log_attrs.extend(['keys', 'correct_resp', 'base_time',
                               'pressed', 'press_time',
                               'correct', 'rt'])

    def _enter(self):
        super(KeyPress, self)._enter()
        # reset defaults
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        self.base_time = val(self.base_time_src)
        if self.base_time is None:
            # set it to the start time
            self.base_time = self.start_time

    def _on_key_down(self, keycode, text, modifiers, event_time):
        # check the key and time (if this is needed)
        keys = val(self.keys)
        correct_resp = val(self.correct_resp)
        sym_str = keycode[1].upper()
        if None in keys or sym_str in keys:
            # it's all good!, so save it
            self.pressed = sym_str
            self.press_time = event_time
            
            # calc RT if something pressed
            self.rt = event_time['time'] - self.base_time

            if self.pressed in correct_resp:
                self.correct = True

            # let's leave b/c we're all done
            self.cancel(event_time['time'])


class KeyRecord(KeyState):
    def __init__(self, duration=None, parent=None, save_log=True, name=None):
        # init the parent class
        super(KeyRecord, self).__init__(parent=parent,
                                        duration=duration,
                                        save_log=save_log,
                                        name=name)

        #...!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def _enter(self):
        super(KeyRecord, self)._enter()
        #...!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def _on_key_down(self, keycode, text, modifiers, event_time):
        print "TODO: Record key down: %r, %r, %r" % (keycode, text, modifiers)  #TODO: actual recording!

    def _on_key_up(self, keycode, event_time):
        print "TODO: Record key up: %r" % (keycode,)  #TODO: actual recording!


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Func, Loop, UntilDone

    def print_dt(state, *args):
        print args

    exp = Experiment()
    Func(print_dt, args=['Press T+G+D or SHIFT+Q+R'])
    Wait(until=((Key("T") & Key("G") & Key("D")) |
                (Key("SHIFT") & Key("Q") & Key("R"))))
    Func(print_dt, args=['Key Press Test'])

    Set('last_pressed','')
    with Loop(conditional=(Get('last_pressed')!='K')):
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Set('last_pressed',kp['pressed'])
        Log(pressed=kp['pressed'], rt=kp['rt'])

    KeyRecord()
    with UntilDone():
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Wait(1.0)

        kp = KeyPress()
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Wait(1.0)

        kp = KeyPress(duration=2.0)
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Wait(1.0)

    exp.run()
    
