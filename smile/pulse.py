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


class Pulse(State):
    """
    State that will wait a specified time in seconds.  It is possible
    to keep the state active or simply move the parent's state time
    ahead.
    """
    def __init__(self, code=15, duration=0.010, port=0,
                 parent=None, reset_clock=False, save_log=True):
        # init the parent class
        super(Pulse, self).__init__(interval=0, parent=parent, 
                                    duration=0, 
                                    reset_clock=reset_clock,
                                    save_log=save_log)
        # Create a parallel port object
        if have_parallel:
            self._pport = parallel.Parallel(port=port)

        self.pulse_code = code
        self.pulse_duration = duration
        self.pulse_port = port

        self.pulse_time = None
        self.pulse_end_time = None

        # append log vars
        self.log_attrs.extend(['pulse_code', 'pulse_duration', 'pulse_port',
                               'pulse_time'])

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
            start_time = now()
            self.pport.setData(ncode)
            end_time = now()

            # set the pulse time
            time_err = (end_time - start_time)/2.
            self.pulse_time = event_time(start_time+time_err,
                                         time_err)

            # schedule the off time
            clock.schedule_once(self._pulse_off_callback, val(self.duration))

    def _pulse_off_callback(dt):
        start_time = now()
        self.pport.setData(0)
        end_time = now()

        # set the pulse time
        time_err = (end_time - start_time)/2.
        self.pulse_end_time = event_time(start_time+time_err,
                                         time_err)



