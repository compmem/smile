#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import CallbackState
from ref import Ref, val
from clock import clock


class MouseState(CallbackState):
    def _on_motion(self, pos, button, newly_pressed, double, triple,
                   event_time):
        pass

    def on_motion(self, pos, button, newly_pressed, double, triple,
                  event_time):
        self.claim_exceptions()
        self._on_motion(pos, button, newly_pressed, double, triple, event_time)

    def _callback(self):
        self.exp.app.add_callback("MOTION", self.on_motion)

    def _leave(self):
        self.exp.app.remove_callback("MOTION", self.on_motion)
        super(MouseState, self)._leave()


class MousePress(MouseState):
    """
    Accept mouse click as response.
    
    Parameters
    -----------
    buttons : {['LEFT', 'RIGHT'], str}
        The button(s) on the mouse that will register as a response.
    correct_resp: {['LEFT', 'RIGHT'], str}
        The correct response to the presented stimulus. 
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
    MousePress(correct_resp='LEFT')
    Participant must make a mouse press response. Responses from both
    buttons will be recorded, but only a 'LEFT' button response will
    be counted as correct
    
 Log Parameters
    ---------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters.      
        press :
            Which button on the mouse was pressed.
        press_time:
            Time at which button was pressed.
        correct:
            Boolean indicator of whether the response was correct
            or incorrect.
        rt: 
            Amount of time that has passed between stimulus onset
            and the participant's response. Dependent upon base_time.  
    
    """
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None):
        # init the parent class
        super(MousePress, self).__init__(parent=parent, 
                                         duration=duration,
                                         save_log=save_log,
                                         name=name)

        # save the buttons we're watching (None for all)
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

        # append log vars
        self.log_attrs.extend(['buttons', 'correct_resp', 'base_time',
                               'pressed', 'press_time', 
                               'correct', 'rt'])

    def _enter(self):
        super(MousePress, self)._enter()
        # reset defaults
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None

    def _callback(self):
        self.base_time = val(self.base_time_src)
        if self.base_time is None:
            # set it to the start time
            self.base_time = self.start_time
        super(MousePress, self)._callback()

    def _on_motion(self, pos, button, newly_pressed, double, triple,
                   event_time):
        if not newly_pressed:
            return

        # check the mouse and time (if this is needed)
        buttons = val(self.buttons)
        button = button.upper()
        correct_resp = val(self.correct_resp)
        if None in buttons or button in buttons:
            # it's all good!, so save it
            self.pressed = button
            self.press_time = event_time
            
            # calc RT if something pressed
            self.rt = event_time['time']-self.base_time

            if self.pressed in correct_resp:
                self.correct = True

            # let's leave b/c we're all done
            self.cancel(event_time['time'])


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Func, Loop

    def print_dt(state, *args):
        print args

    exp = Experiment()
    
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
