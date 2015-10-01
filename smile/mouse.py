#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import operator

import kivy_overrides
from kivy.core.window import Window
import kivy.graphics
from kivy.core.image import Image

from state import CallbackState, Record
from ref import Ref, val, NotAvailable
from clock import clock
from experiment import Experiment
from video import VisualState


def MouseWithin(widget):
    pos = Experiment._last_instance()._app.mouse_pos_ref
    return ((pos[0] >= widget.x) & (pos[1] >= widget.y) &
            (pos[0] <= widget.right) & (pos[1] <= widget.top))


def MousePos(widget=None):
    pos = Experiment._last_instance()._app.mouse_pos_ref
    if widget is None:
        return pos
    else:
        return Ref.cond(MouseWithin(widget),
                        Ref(map, operator.sub, pos, widget.pos),
                        None)


def MouseButton(widget=None):
    button = Experiment._last_instance()._app.mouse_button_ref
    if widget is None:
        return button
    else:
        return Ref.cond(MouseWithin(widget), button, None)


def MouseRecord(widget=None, name="MouseRecord"):
    rec = Record(pos=MousePos(widget), button=MouseButton(widget), name=name)
    rec.override_instantiation_context()
    return rec


class MouseCursor(VisualState):
    stack = []
    def __init__(self, filename=None, offset=None, duration=None, parent=None,
                 save_log=True, name=None, blocking=True):
        super(MouseCursor, self).__init__(parent=parent, 
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)
        if filename is None:
            self._init_filename = "crosshairs.png"  #TODO: this must always look in the smile source directory!
            self._init_offset = (50, 50)
        else:
            self._init_filename = filename
            self._init_offset = offset

        self.__instruction = None
        self.__color_instruction = kivy.graphics.Color(1.0, 1.0, 1.0, 1.0)
        self.__pos_ref = self._exp._app.mouse_pos_ref

        self._log_attrs.extend(["filename", "offset"])

    def _enter(self):
        super(MouseCursor, self)._enter()
        texture = Image(self._filename).texture
        self.__instruction = kivy.graphics.Rectangle(texture=texture,
                                                     size=texture.size)

    def show(self):
        if len(MouseCursor.stack):
            MouseCursor.stack.pop()._remove_from_canvas()
        self._add_to_canvas()
        MouseCursor.stack.append(self)

    def _add_to_canvas(self):
        Window.canvas.after.add(self.__color_instruction)
        Window.canvas.after.add(self.__instruction)
        self.__pos_ref.add_change_callback(self._update_position)
        self._update_position()

    def _remove_from_canvas(self):
        Window.canvas.after.remove(self.__color_instruction)
        Window.canvas.after.remove(self.__instruction)
        self.__pos_ref.remove_change_callback(self._update_position)

    def _update_position(self):
        pos = val(self.__pos_ref)
        if None not in pos:
            self.__instruction.pos = [mp - os for (mp, os) in
                                      zip(pos, self._offset)]

    def unshow(self):
        if MouseCursor.stack[-1] is self:
            self._remove_from_canvas()
            MouseCursor.stack.pop()
            try:
                MouseCursor.stack[-1]._add_to_canvas()
            except IndexError:
                pass
        else:
            MouseCursor.stack.remove(self)


class MousePress(CallbackState):
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 widget=None, duration=None, parent=None, save_log=True,
                 name=None, blocking=True):
        super(MousePress, self).__init__(parent=parent, 
                                         duration=duration,
                                         save_log=save_log,
                                         name=name,
                                         blocking=blocking)
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

    def _enter(self):
        super(MousePress, self)._enter()
        if self._base_time is None:
            self._base_time = self._start_time
        if self._buttons is None:
            self._buttons = []
        elif type(self._buttons) not in (list, tuple):
            self._buttons = [self._buttons]
        if self._correct_resp is None:
            self._correct_resp = []
        elif type(self.correct_resp) not in (list, tuple):
            self._correct_resp = [self._correct_resp]
        self._pressed = NotAvailable
        self._press_time = NotAvailable
        self._correct = NotAvailable
        self._rt = NotAvailable
        self._pos = NotAvailable

    def _callback(self):
        self.__button_ref.add_change_callback(self.button_callback)

    def button_callback(self):
        self.claim_exceptions()
        button = self.__button_ref.eval()
        if button is None:
            return
        button = button.upper()
        if not len(self._buttons) or button in self._buttons:
            # it's all good!, so save it
            self._pressed = button
            self._press_time = self._exp._app.event_time
            
            # calc RT if something pressed
            self._rt = self._press_time['time'] - self._base_time

            self._pos = self.__pos_ref.eval()

            if self._pressed in self._correct_resp:
                self._correct = True

            # let's leave b/c we're all done
            self.cancel(self._press_time['time'])

    def _leave(self):
        self.__button_ref.remove_change_callback(self.button_callback)
        super(MousePress, self)._leave()
        if self._pressed is NotAvailable:
            self._pressed = ''
        if self._press_time is NotAvailable:
            self._press_time = None
        if self._correct is NotAvailable:
            self._correct = False
        if self._rt is NotAvailable:
            self._rt = None
        if self._pos is NotAvailable:
            self._pos = (None, None)


if __name__ == '__main__':

    from experiment import Experiment
    from state import Wait, Debug, Loop, Meanwhile, Record, Log, Parallel

    def print_dt(state, *args):
        print args

    exp = Experiment()

    with Meanwhile():
        #Record(pos=MousePos(), button=MouseButton())
        with Parallel():
            MouseRecord()
            MouseCursor()

    Debug(name='Mouse Press Test')

    exp.last_pressed = ''
    with Loop(conditional=(exp.last_pressed!='RIGHT')):
        kp = MousePress(buttons=['LEFT','RIGHT'], correct_resp='RIGHT')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        exp.last_pressed = kp.pressed
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
