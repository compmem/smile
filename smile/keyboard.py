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
        self._exp.app.add_callback("KEY_DOWN", self.on_key_down)
        self._exp.app.add_callback("KEY_UP", self.on_key_up)

    def _leave(self):
        self._exp.app.remove_callback("KEY_DOWN", self.on_key_down)
        self._exp.app.remove_callback("KEY_UP", self.on_key_up)
        super(KeyState, self)._leave()


class KeyPress(KeyState):
    def __init__(self, keys=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None):
        # init the parent class
        super(KeyPress, self).__init__(parent=parent,
                                       duration=duration,
                                       save_log=save_log,
                                       name=name)

        self._init_keys = keys
        self._init_correct_resp = correct_resp
        self._init_base_time = base_time
        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None

        # append log vars
        self._log_attrs.extend(['keys', 'correct_resp', 'base_time',
                                'pressed', 'press_time',
                                'correct', 'rt'])

    def _enter(self):
        super(KeyPress, self)._enter()
        # reset defaults
        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None
        if self._base_time is None:
            self._base_time = self.start_time

    def _on_key_down(self, keycode, text, modifiers, event_time):
        if type(self._keys) in (list, tuple):
            keys = self._keys
        else:
            keys = [self.keys]
        if type(self._correct_resp) in (list, tuple):
            correct_resp = self._correct_resp
        else:
            correct_resp = [self._correct_resp]
        sym_str = keycode[1].upper()
        if None in keys or sym_str in keys:
            # it's all good!, so save it
            self._pressed = sym_str
            self._press_time = event_time
            
            # calc RT if something pressed
            self._rt = event_time['time'] - self._base_time

            if self._pressed in correct_resp:
                self._correct = True

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
    from state import Wait, Debug, Loop, UntilDone

    exp = Experiment()
    Debug(name='Press T+G+D or SHIFT+Q+R')
    Wait(until=((Key("T") & Key("G") & Key("D")) |
                (Key("SHIFT") & Key("Q") & Key("R"))))
    Debug(name='Key Press Test')

    Set(last_pressed='')
    with Loop(conditional=(Get('last_pressed')!='K')):
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Set(last_pressed=kp.pressed)
        Log(pressed=kp.pressed, rt=kp.rt)

    KeyRecord()
    with UntilDone():
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

        kp = KeyPress()
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

        kp = KeyPress(duration=2.0)
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

    exp.run()
    
