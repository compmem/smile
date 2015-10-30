#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import operator
import os

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
    """Developer Use Only"""
    pos = Experiment._last_instance()._app.mouse_pos_ref
    return ((pos[0] >= widget.x) & (pos[1] >= widget.y) &
            (pos[0] <= widget.right) & (pos[1] <= widget.top))


def MousePos(widget=None):
    """Developer Use Only"""
    pos = Experiment._last_instance()._app.mouse_pos_ref
    if widget is None:
        return pos
    else:
        return Ref.cond(MouseWithin(widget),
                        Ref(map, operator.sub, pos, widget.pos),
                        None)


def MouseButton(widget=None):
    """Developer Use Only"""
    button = Experiment._last_instance()._app.mouse_button_ref
    if widget is None:
        return button
    else:
        return Ref.cond(MouseWithin(widget), button, None)


def MouseRecord(widget=None, name="MouseRecord"):
    """Developer Use Only"""
    rec = Record(pos=MousePos(widget), button=MouseButton(widget), name=name)
    rec.override_instantiation_context()
    return rec


class MouseCursor(VisualState):
    """A *MouseCursor* state will tell your experiment to show your cursor. By default, 
    your cursor is hidden and doesnt send any feedback to your experiment.  
    
    Parameters
    ----------
    filename : string (optional)
        The filename of a replacement cursor image. Will show this image instead of the arrow.
    offset : tuple (optional)
        The pixel offset of the image and the center of the cursor. Defaults to (50, 50) for 
        our default 100x100 pixel cursor image, that way the center of the image is right at 
        the end of the arrow on a regular cursor.
    duration : float (optional)
        The duration of this state. If None is given, then the state will not set an end time 
        and run until canceled. 
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set, the *Experiment* will
        make it a child of a ParentState or the Experiment automatically.
    save_log : boolean (default = True, optional)
        If True, save out a .slog file contianing all of the information for this *Wait* state. 
    name : string (optional)
        The unique name of this state
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If False, this state will
        be canceled if its Parallel Parent finishes running. Only relevent if within a *Parallel* Parent.
    
    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state-specific log. Refer to State class
    docstring for addtional logged parameters. 

    instantiation_filename : string
        The file in which this state is instantiated. 
    instantiation_lineno : int
        the line number that this particular state was instantiated
    name : string
        The unique name given to this state
    start_time : float
        The time the state was started in experimental runtime
    end_time : float
        The time this state ended in experimental runtime
    enter_time : float
        The time this state entered and started all of it's preprocessing in experimental
        runtime.
    leave_time : float
        The time this state left, calling callbacks, and ending processes in experimental runtime. 
    finalize_time : float
        The time this state
    filename : string
        Filename of the cursor you are using. 
    offest : tuple
        X and Y offset of the cursor.
    """
    stack = []
    def __init__(self, filename=None, offset=None, duration=None, parent=None,
                 save_log=True, name=None, blocking=True):
        super(MouseCursor, self).__init__(parent=parent, 
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)
        if filename is None:
            self._init_filename = os.path.join(os.path.dirname(__file__),
                                               "crosshairs.png")
            self._init_offset = (50, 50)
        else:
            self._init_filename = filename
            self._init_offset = offset

        self.__texture = None
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
        try:
            MouseCursor.stack[-1]._remove_from_canvas()
        except IndexError:
            pass
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
    """A *MousePress* state will tell your experiment to record the buttons pressed, but not 
    show the cursor. By default, your cursor is hidden and doesnt send any feedback to your 
    experiment. You call *MousePress* like you would call *KeyPress* in that you can tell it
    what buttons are valid input, and what the correct input is.  
    
    Parameters
    ----------
    buttons : list (optional)
        Give a list of mouse buttons names that the participant can press, all uppercase letters. 
        Example : ``['LEFT', 'RIGHT']``
    correct_resp : list (optional)
        If None, then every answer is incorrect. If given a list of strings, even if it is one string
        in length, any buttons in that list of strings will be concidered correct. 
    base_time : float (optional)
        If you would like the timing of the button press's reaction time to be based on the appear time 
        a stimulus, you put that value here. 
    widget : widget (optional)
        If you would like the mouse to appear only within a another visual state, like a *Rectangle* or a 
        *Label*, then you pass in that visual state here. 
    duration : float (optional)
        The duration of this state. If None is given, then the state will not set an end time 
        and run until canceled. 
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set, the *Experiment* will
        make it a child of a ParentState or the Experiment automatically.
    save_log : boolean (default = True, optional)
        If True, save out a .slog file contianing all of the information for this *Wait* state. 
    name : string (optional)
        The unique name of this state
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If False, this state will
        be canceled if its Parallel Parent finishes running. Only relevent if within a *Parallel* Parent.
    
    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state-specific log. Refer to State class
    docstring for addtional logged parameters. 

    instantiation_filename : string
        The file in which this state is instantiated. 
    instantiation_lineno : int
        the line number that this particular state was instantiated
    name : string
        The unique name given to this state
    start_time : float
        The time the state was started in experimental runtime
    end_time : float
        The time this state ended in experimental runtime
    enter_time : float
        The time this state entered and started all of it's preprocessing in experimental
        runtime.
    leave_time : float
        The time this state left, calling callbacks, and ending processes in experimental runtime. 
    finalize_time : float
        The time this state
    buttons : list
        A list of strings with the names of buttons that are valid and this *MousePress*
        state is listening for. 
    correct_resp : string, tuple, list
        A string, tuple, or list of strings that contain the names of correct button responses
        for this *MousePress*.
    base_time : float
        The base from which later timing is associated.
    pressed : string
        The name of the button they pressed.
    press_time : float
        The time in which they pressed a mouse button
    correct : boolean  
        Whether they pressed the **correct_resp** button or not. 
    rt : float
        The reaction time associated with a mouse press. **press_time** - **base_time**
    pos : tuple
        A tuple, (x,y), that is the position of the mouse button press. 
    """
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
        elif type(self._correct_resp) not in (list, tuple):
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

    Wait(2.0)
    MouseCursor("face-smile.png", (125, 125), duration=5.0)

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
