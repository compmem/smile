#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .state import CallbackState
from .ref import val, NotAvailable
from .ref import Ref, val, NotAvailable
from .experiment import Experiment

import math


def JoyButton(buttonid):
    """Grab reference to a JoyButton"""
    exp = Experiment._last_instance()
    return exp.screen._get_joybutton_ref(buttonid)


class JoyButtonState(CallbackState):
    """For developer use only"""
    def __init__(self, parent=None, duration=None, save_log=True, name=None,
                 blocking=True):
        super(JoyButtonState, self).__init__(parent=parent, duration=duration,
                                             save_log=save_log, name=name,
                                             blocking=blocking)

    def on_button_down(self, buttonid, event_time):
        self.claim_exceptions()
        self._on_button_down(buttonid, event_time)

    def _on_button_down(self, buttonid, event_time):
        pass

    def on_button_up(self, buttonid, event_time):
        self.claim_exceptions()
        self._on_button_up(buttonid, event_time)

    def _on_button_up(self, buttonid, event_time):
        pass

    def _callback(self):
        self._exp._app.add_callback("JOYBUTTON_DOWN", self.on_button_down)
        self._exp._app.add_callback("JOYBUTTON_UP", self.on_button_up)

    def _leave(self):
        self._exp._app.remove_callback("JOYBUTTON_DOWN", self.on_button_down)
        self._exp._app.remove_callback("JOYBUTTON_UP", self.on_button_up)
        super(JoyButtonState, self)._leave()


class JoyPress(JoyButtonState):
    """A state that listens for a joystick button press.

    A *JoyPress* state will wait for a duration, if there is one, for a button
    that is within the **buttons** list and then tell you if they picked a
    response that was within the **correct_resp** list, and tell you the
    response time.

    Parameters
    ----------
    buttons : list (optional)
        A list of valid buttonid in the form of integers. If no
        list is provided, any button can be pressed to continue past this state.
    correct_resp : list, tuple, int (optional)
        A list, tuple, or string, containing the names of any buttons that
        would be considered a correct response.
    base_time : float (optional)
        If you need to record the time of the response precisely in
        relation to the timing of another state, you put that here.
        Example: If you would want to know exactly how long after a *Label*
        state appears on the screen, you would set **base_time** to
        lb.appear_time['time']
    duration : float (optional)
        The duration you would like your experiment to wait for a buttonpress.
        If set to None, then it will wait until a button from **buttons** is
        pressed, then continue with the experiment.
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set,
        the *Experiment* will make it a child of a ParentState or the
        Experiment automatically.
    save_log : boolean (default = True, optional)
        If True, save out a .slog file containing all of the information
        for this state.
    name : string (optional)
        The unique name of this state
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its Parallel Parent finishes
        running. Only relevant if within a *Parallel* Parent.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    pressed : int
        The id of the button they pressed.
    press_time : float
        The time in which they pressed a buttonboard button
    correct : boolean
        Whether they pressed the **correct_resp** button or not.
    rt : float
        The reaction time associated with a button press.
        **press_time** - **base_time**

    Example
    -------

    ::

        Label(text='These are your instructions, press ENTER to continue')
        with UntilDone():
            kp = JoyPress(buttons=[0,2])

    This will show the instruction *Label* until either the 0 or 2 button
    is pressed.

    """
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(JoyPress, self).__init__(parent=parent,
                                       duration=duration,
                                       save_log=save_log,
                                       name=name,
                                       blocking=blocking)

        self._init_buttons = buttons
        self._init_correct_resp = correct_resp
        self._init_base_time = base_time
        self._pressed = None
        self._press_time = None
        self._correct = False
        self._rt = None

        # append log vars
        self._log_attrs.extend(['buttons', 'correct_resp', 'base_time',
                                'pressed', 'press_time',
                                'correct', 'rt'])

    def _enter(self):
        super(JoyPress, self)._enter()
        # reset defaults
        self._pressed = NotAvailable
        self._press_time = NotAvailable
        self._correct = NotAvailable
        self._rt = NotAvailable
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

    def _on_button_down(self, buttonid, event_time):
        if not len(self._buttons) or buttonid in self._buttons:
            # we have a matching button press, so save it
            self._pressed = buttonid
            self._press_time = event_time

            # calc RT if something pressed
            self._rt = event_time['time'] - self._base_time

            self._correct = self._pressed in self._correct_resp

            # let's leave b/c we're all done
            self.cancel(event_time['time'])

    def _leave(self):
        super(JoyPress, self)._leave()
        if self._pressed is NotAvailable:
            self._pressed = None
        if self._press_time is NotAvailable:
            self._press_time = None
        if self._correct is NotAvailable:
            self._correct = False
        if self._rt is NotAvailable:
            self._rt = None


# Joystick Axis Processing

MAX_JOY_AXIS = 32767

def JoyAxis(axisid, scaled=True):
    """Return reference to a joystick axis"""
    joyax = Experiment._last_instance().screen.get_joyaxis_value(axisid)
    if scaled:
        joyax = joyax / MAX_JOY_AXIS
    return joyax

def JoyAxesToPolar(axisid0, axisid1, scaled=True):
    """Return references to radius and theta from a pair of joystick axes."""
    axis0 = JoyAxis(axisid0, scaled=scaled)
    axis1 = JoyAxis(axisid1, scaled=scaled)
    
    radius = Ref(math.sqrt, axis0**2 + axis1**2)
    theta = Ref(math.atan2, axis1, axis0)

    return radius, theta
    
