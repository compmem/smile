#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import sys
from pyglet import clock
try:
    import parallel
    have_parallel = True
except ImportError:
    sys.stderr.write("\nWARNING: The parallel module could not load,\n" + 
                     "\tso no sync pulsing will be generated.\n\n")
    have_parallel = False


from state import State
from ref import Ref, val
from experiment import now,event_time


class Pulse(State):
    """
    State that will send a sync pulse out the parallel port.
    
    Parameters
    ----------
    code : int
    duration : {0.0, float}
        Time in seconds that the pulse is on. Default is 0.010 s.
    port : {0, 255, int}
        Value specifying the trigger byte.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    save_log : bool
        If set to 'True,' details about the state will be
        automatically saved in the log files. 
        
    Example
    --------
    Pulse(code=1)
    A sync pulse will be sent and will register 'S1' as the code
    on both the presentation machine and the EEG apparatus.
    
    Log Parameters
    ---------------
    All of the above parameters for each Pulse state will be 
    recorded in the state.yaml and state.csv files, along with the
    parameters specified in State documentation.
    """
    def __init__(self, code=15, duration=0.010, port=0,
                 parent=None, save_log=True):
        # init the parent class
        super(Pulse, self).__init__(interval=0, parent=parent, 
                                    duration=0, 
                                    save_log=save_log)
        # save the info
        self.pulse_code = code
        self.pulse_duration = duration
        self.pulse_port = port

        self.pulse_time = None
        self.pulse_end_time = None

        # append log vars
        self.log_attrs.extend(['pulse_code', 'pulse_duration', 'pulse_port',
                               'pulse_time', 'pulse_end_time'])

    def _callback(self, dt):        
        # Convert code if necessary
        code = val(self.pulse_code)
        if type(code)==str:
            if code[0]=="S":
                # Use first 4 bits
                ncode = int(code[1:])
                if ncode < 0 or ncode > 16: ncode = 15
            elif code[0]=="R":
                # Use last 4 bits
                ncode = int(code[1:])
                if ncode < 0 or ncode > 16: ncode = 15
                ncode = ncode >> 4
            else:
                # Convert to an integer
                ncode = int(code)
        else:
            ncode = int(code)

        # send the code
        if have_parallel:
            # Create a parallel port object (locks it exclusively)
            self._pport = parallel.Parallel(port=self.pulse_port)

            # send the port code and time it
            start_time = now()
            self._pport.setData(ncode)
            end_time = now()

            # set the pulse time
            time_err = (end_time - start_time)/2.
            self.pulse_time = event_time(start_time+time_err,
                                         time_err)

            # schedule the off time
            clock.schedule_once(self._pulse_off_callback, val(self.pulse_duration))

    def _pulse_off_callback(self, dt):
        # turn off the code
        start_time = now()
        self._pport.setData(0)
        end_time = now()

        # clean up / close the port
        self._pport = None

        # set the pulse time
        time_err = (end_time - start_time)/2.
        self.pulse_end_time = event_time(start_time+time_err,
                                         time_err)



