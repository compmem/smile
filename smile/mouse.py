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

class MousePress(CallbackState):
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
    def __init__(self, buttons=None, correct_resp=None, base_time=None, until=None,
                 duration=-1, parent=None, save_log=True):
        # init the parent class
        super(MousePress, self).__init__(interval=-1, parent=parent, 
                                         duration=-1,
                                         save_log=save_log)

        # save the buttons we're watching (None for all)
        if not isinstance(buttons, list):
            buttons = [buttons]
        self.buttons = buttons
        if not isinstance(correct_resp, list):
            correct_resp = [correct_resp]
        self.correct_resp = correct_resp
        self.base_time_src = base_time  # for calc rt
        self.base_time = None
        self.wait_duration = duration
        self.wait_until = until

        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        
        # if wait duration is -1 wait indefinitely

        # if a wait_duration is specified, that's how long to look for
        # mousepresses.

        # we're not waiting yet
        self.waiting = False

        # append log vars
        self.log_attrs.extend(['buttons', 'correct_resp', 'base_time',
                               'pressed', 'press_time', 
                               'correct', 'rt'])

    def _enter(self):
        # reset defaults
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None

    def _mouse_callback(self, x, y, button, modifiers, event_time):
        # check the mouse and time (if this is needed)
        buttons = val(self.buttons)
        correct_resp = val(self.correct_resp)
        button_str = mouse.buttons_string(button)
        if None in buttons or button_str in buttons:
            # it's all good!, so save it
            self.pressed = button_str
            self.press_time = event_time

            # fill the base time val
            self.base_time = val(self.base_time_src)
            if self.base_time is None:
                # set it to the state time
                self.base_time = self.state_time
            
            # calc RT if something pressed
            self.rt = event_time['time']-self.base_time

            if self.pressed in correct_resp:
                self.correct = True

            # let's leave b/c we're all done
            #self.interval = 0
            self.leave()
            
    def _callback(self, dt):
        if not self.waiting:
            self.exp.window.mouse_callbacks.append(self._mouse_callback)
            self.waiting = True
        wait_duration = val(self.wait_duration)
        if ((wait_duration > 0 and now() >= self.state_time+wait_duration) or
            (val(self.wait_until))):
            # we're done
            self.leave()
            #self.interval = 0
            
    def _leave(self):
        # remove the mouseboard callback
        self.exp.window.mouse_callbacks.remove(self._mouse_callback)
        self.waiting = False
        pass
    


if __name__ == '__main__':

    from experiment import Experiment, Get, Set, Log
    from state import Wait, Func, Loop

    def print_dt(state, *args):
        print args, state.dt

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
    Wait(1.0, stay_active=True)

    exp.run()
