#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import CallbackState, Record
from ref import Ref, val
from clock import clock
from experiment import Experiment
import operator


def MouseWithin(widget):
    pos = Experiment.last_instance().app.mouse_pos_ref
    return (pos[0] >= widget['x'] & pos[1] >= widget['y'] &
            pos[0] <= widget['right'] & pos[1] <= widget['top'])


def MousePos(widget=None):
    pos = Experiment.last_instance().app.mouse_pos_ref
    if widget is None:
        return pos
    else:
        return Ref.cond(MouseWithin(widget),
                        Ref(map, operator.sub, pos, widget['pos']),
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
        if not isinstance(buttons, list):
            buttons = [buttons]
        self.buttons = buttons
        if not isinstance(correct_resp, list):
            correct_resp = [correct_resp]
        self.correct_resp = correct_resp
        self.base_time_src = base_time  # for calc rt
        self.base_time = None

        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        self.pos = None

        self.pos_ref = MousePos(widget)
        self.button_ref = MouseButton(widget)

        # append log vars
        self.log_attrs.extend(['buttons', 'correct_resp', 'base_time',
                               'pressed', 'press_time', 
                               'correct', 'rt', 'pos'])

    def _callback(self):
        self.base_time = val(self.base_time_src)
        if self.base_time is None:
            self.base_time = self.start_time
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        self.pos = None
        self.button_ref.add_change_callback(self.button_callback)

    def button_callback(self):
        button = self.button_ref.eval()
        if button is None:
            return
        button = button.upper()
        buttons = val(self.buttons)
        correct_resp = val(self.correct_resp)
        if None in buttons or button in buttons:
            # it's all good!, so save it
            self.pressed = button
            self.press_time = self.exp.app.event_time
            
            # calc RT if something pressed
            self.rt = self.press_time['time'] - self.base_time

            self.pos = self.pos_ref.eval()

            if self.pressed in correct_resp:
                self.correct = True

            # let's leave b/c we're all done
            self.cancel(self.press_time['time'])

    def _leave(self):
        self.button_ref.remove_change_callback(self.button_callback)
        super(MousePress, self)._leave()


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Func, Loop, Meanwhile, Record

    def print_dt(state, *args):
        print args

    exp = Experiment()

    with Meanwhile():
        #Record(pos=MousePos(), button=MouseButton())
        MouseRecord()
    
    Func(print_dt, args=['Mouse Press Test'])

    Set('last_pressed','')
    with Loop(conditional=(Get('last_pressed')!='RIGHT')):
        kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
        Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
        Set('last_pressed',kp['pressed'])
        Log(pressed=kp['pressed'], rt=kp['rt'])
    
    kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = MousePress()
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    kp = MousePress(duration=2.0)
    Func(print_dt, args=[kp['pressed'],kp['rt'],kp['correct']])
    Wait(1.0)

    exp.run()
