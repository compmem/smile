#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import operator

from state import CallbackState, Record
from ref import Ref, val
from clock import clock
from experiment import Experiment


def MouseWithin(widget):
    pos = Experiment.last_instance().app.mouse_pos_ref
    return (pos[0] >= widget.x & pos[1] >= widget.y &
            pos[0] <= widget.right & pos[1] <= widget.top)


def MousePos(widget=None):
    pos = Experiment.last_instance().app.mouse_pos_ref
    if widget is None:
        return pos
    else:
        return Ref.cond(MouseWithin(widget),
                        Ref(map, operator.sub, pos, widget.pos),
                        None)


def MouseButton(widget=None):
    button = Experiment.last_instance().app.mouse_button_ref
    if widget is None:
        return button
    else:
        return Ref.cond(MouseWithin(widget), button, None)


def MouseRecord(widget=None, name="MouseRecord"):
    rec = Record(pos=MousePos(widget), button=MouseButton(widget), name=name)
    rec.override_instantiation_context()
    return rec


class MousePress(CallbackState):
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 widget=None, duration=None, parent=None, save_log=True,
                 name=None):
        super(MousePress, self).__init__(parent=parent, 
                                         duration=duration,
                                         save_log=save_log,
                                         name=name)
        self._init_buttons = buttons
        self._init_correct_resp = correct_resp
        self._init_base_time = base_time

        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None
        self._pos = None

        self.__pos_ref = MousePos(widget)
        self.__button_ref = MouseButton(widget)

        # append log vars
        self._log_attrs.extend(['buttons', 'correct_resp', 'base_time',
                                'pressed', 'press_time', 
                                'correct', 'rt', 'pos'])

    def _callback(self):
        if self._base_time is None:
            self._base_time = self._start_time
        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None
        self._pos = None
        self.__button_ref.add_change_callback(self.button_callback)

    def button_callback(self):
        self.claim_exceptions()
        button = self.__button_ref.eval()
        if button is None:
            return
        button = button.upper()
        if type(self._buttons) in (list, tuple):
            buttons = self._buttons
        else:
            buttons = [self._buttons]
        if type(self._correct_resp) in (list, tuple):
            correct_resp = self._correct_resp
        else:
            correct_resp = [self._correct_resp]
        if None in buttons or button in buttons:
            # it's all good!, so save it
            self._pressed = button
            self._press_time = self._exp.app.event_time
            
            # calc RT if something pressed
            self._rt = self._press_time['time'] - self._base_time

            self._pos = self.__pos_ref.eval()

            if self._pressed in correct_resp:
                self._correct = True

            # let's leave b/c we're all done
            self.cancel(self._press_time['time'])

    def _leave(self):
        self.__button_ref.remove_change_callback(self.button_callback)
        super(MousePress, self)._leave()


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Debug, Loop, Meanwhile, Record

    def print_dt(state, *args):
        print args

    exp = Experiment()

    with Meanwhile():
        #Record(pos=MousePos(), button=MouseButton())
        MouseRecord()
    
    Debug(name='Mouse Press Test')

    Set(last_pressed='')
    with Loop(conditional=(Get('last_pressed')!='RIGHT')):
        kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Set(last_pressed=kp.pressed)
        Log(pressed=kp.pressed, rt=kp.rt)
    
    kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

    kp = MousePress()
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

    kp = MousePress(duration=2.0)
    Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
    Wait(1.0)

    exp.run()
