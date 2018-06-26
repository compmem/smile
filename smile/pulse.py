#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import sys
from smile.state import Wait, State, Loop, Done, Log, Subroutine
from smile.clock import clock
from smile.event import event_time
from smile.ref import NotAvailable

# Interface Class for Docstrings
class PulseInterface(object):
    """The interface for creating a Parallel Port Interface

    SMILE uses a standard interface for using the ParallelPort drivers. This
    is a blank interface for the purpose of expressing the required functions
    needed if you wanted to create your own Parallel Port Interface. """
    def __init__(self, address):
        """The init for the interface.

        Depending on what module you use to send sync pulsing, the addressing
        system will be different. For example, Inpout32 uses a binary address
        system i.e. 0xD010. parallel for Linux for example uses a port system,
        and simply putting the address as an integer like 0 or 1 will allow
        it to work.

        It is recommended that if you are using a windows system to look up
        what your port number is via device manager. """
        return
    def setData(self, data):
        return

# PI set to none for if the creation of a Parallel Interface fails.
PI = None

# Find out what platform to import for
if sys.platform.startswith('linux'):
    # If Linux, try pyparallel
    try:
        import parallel
        class LinuxP(PulseInterface):
            def __init__(self, address):
                """Setup Port"""
                self._port = parallel.Parallel(port=address)

            def setData(self, data):
                """Write Data"""
                self._port.setData(data)

        PI = LinuxP
    except:
        # If the import fails, let them know that
        # pyparallel didn't load properly.
        sys.stderr.write("\nWARNING: The parallel module pyparallel could not load,\n" +
                         "\tso no parallel sync pulsing will be available.\n\n")
elif sys.platform.startswith('win'):
    # If Windows, try Inpout32, right now, required to be in the
    # same folder as the experiment.
    try:
        from ctypes import windll
        class ParallelInpout32(PulseInterface):
            def __init__(self, address):
                """Setup the port"""
                self._port = windll.inpout32
                self.base = address
                BYTEMODEMASK = 0x11100000

                # Make sure that the port is in BYTE MODE
                _inp = self._port.Inp32(self.base + 0x402)
                self._port.Out32(self.base + 0x402,
                                 int((_inp & ~BYTEMODEMASK) | (1 << 5)))

                # Make sure that the port is in OUTPUT MODE
                _inp = self._port.Inp32(self.base + 2)
                self._port.Out32(self.base + 2,
                                 int(_inp & ~(0x00100000)))
            def setData(self, data):
                """Write Data"""
                self._port.Out32(self.base, data)

        # Set the global *Parallel Interface* variable.
        PI = ParallelInpout32
    except:
        # If the import fails, let them know they might need
        # to install Inpout32
        sys.stderr.write("\nWARNING: The parallel module inpout32 could not load,\n" +
                         "\tso no parallel sync pulsing will be available.\n\n")
else:
    # If not Linux or Widnows, tell them they can't load the module.
    sys.stderr.write("\nWARNING: The parallel module could not load,\n" +
                     "\tso no parallel sync pulsing will be available.\n\n")

# PI set to none for if the creation of a Parallel Interface fails.
SI = None

# Find out what platform to import for
try:
    import serial
    class SerialPySerial(PulseInterface):
        """Serial sync pulsing via PySerial.

        Works with both virtual usb serial ports and hardware serial ports."""
        def __init__(self, address="COM4", baud=57600,
                     data_size=8, stop_size=1):
            """Setup the port.

            The address, baud, data size, and stop size should be set to match
            the requirements of your system."""

            self._port = serial.Serial(port=address, baudrate=baud,
                                       bytesize=data_size, stopbits=stop_size)
        def setData(self, data):
            """Write Data, Must be an iterable object"""
            self._port.write(data)
    # Set the global *Serial Interface* to SerialPySerial
    SI = SerialPySerial
except:
    sys.stderr.write("\nWARNING: The serial module pyserial could not load,\n" +
                     "\tso no serial sync pulsing will be available.\n\n")

class Pulse(State):
    """
    Send a sync pulse out the parallel port.

    Parameters
    ----------
    code : {0, 255, integer}, string
        Value specifying the trigger byte. Can be int or str.
    width : {0.010, float}
        Time in seconds that the pulse is on. Default is 0.010 s.
        If the width is 0.0, the code is set and kept.
    port :
        Port where to send the code
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    save_log : boolean
        If set to 'True,' details about the state will be
        automatically saved in the log files.
    name : string
        Name of the state for debugging and tracking

    Logged Attributes
    ---------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for addtional logged parameters.

    code_num :
        Number derived from the code.
    pulse_on :
        Time at which the pulse began.
    pulse_off :
        Time at which the pulse ended.

    Example
    --------

    ::

        Pulse(code=1)

    A sync pulse will be sent and will register 'S1' as the code
    on both the presentation machine and the EEG apparatus.

    """
    def __init__(self, code=15, width=0.010, port=0,
                 parent=None, save_log=True, name=None,
                 sync_style="parallel"):
        # init the parent class
        super(Pulse, self).__init__(parent=parent,
                                    duration=0,
                                    save_log=save_log,
                                    name=name)
        # handle the values that could require initialization
        self._init_code = code
        self._init_width = width
        self._init_port = port

        self._pulse_on = NotAvailable
        self._pulse_off = NotAvailable

        self._sync_style = sync_style

        # append log vars
        self.log_attrs.extend(['code', 'code_num', 'width', 'port',
                               'pulse_on', 'pulse_off'])

    def _enter(self):
        # process the parent enter
        super(Pulse, self)._enter()

        # pulse times are not avail
        self._pulse_on = NotAvailable
        self._pulse_off = NotAvailable

        if self._sync_style == "parallel":
            # Convert code if necessary
            if type(self._code) == str:
                if self._code[0] == "S":
                    # Use first 4 bits
                    ncode = int(self._code[1:])
                    if ncode < 0 or ncode > 16:
                        ncode = 15
                elif self._code[0] == "R":
                    # Use last 4 bits
                    ncode = int(self._code[1:])
                    if ncode < 0 or ncode > 16:
                        ncode = 15
                    ncode = ncode >> 4
                else:
                    # Convert to an integer
                    ncode = int(self._code)
            else:
                ncode = int(self._code)
            self._code_num = ncode

    def _schedule_start(self):
        clock.schedule(self._callback, event_time=self._start_time)

    def _unschedule_start(self):
        clock.unschedule(self._callback)

    def _callback(self):
        # we've started
        self._started = True
        # Pull in the global variables
        global PI
        global SI
        if PI or SI:
            # send the port code and time it
            try:
                if self._sync_style == "parallel":
                    # Create a parallel port object
                    # from the global variable (locks it exclusively)
                    self._sport = PI(address=self._port)
                    start_time = clock.now()
                    self._sport.setData(self._code_num)
                    end_time = clock.now()
                elif self._sync_style == "serial":
                    self._sport = SI(address=self._port)
                    start_time = clock.now()
                    self._sport.setData(self._code_num)
                    end_time = clock.now()
            except:  # eventually figure out which errors to catch
                sys.stderr.write("\nWARNING: The sync module could not send pulses,\n" +
                                 "\tso no sync pulsing will be generated.\n\n")
                PI = None
                self._pport = None
                self._pulse_on = None
                self._pulse_off = None
                self._ended = True
                clock.schedule(self.leave)
                clock.schedule(self.finalize)
                return

            # set the pulse time
            time_err = (end_time - start_time)/2.
            self._pulse_on = event_time(start_time+time_err,
                                        time_err)

            # schedule leaving (as soon as this method is done)
            clock.schedule(self.leave)

            # schedule the off time
            if self._width > 0.0:
                # we're gonna turn off ourselves
                clock.schedule(self._pulse_off_callback,
                               event_time=self._pulse_on['time']+self._width)
            else:
                # we're gonna leave it
                self._pulse_off = None

                # clean up/ close the port
                self._sport = None

                # so we can finalize now, too
                clock.schedule(self.finalize)
                self._ended = True

        else:
            # we can leave and finalize now
            self._pulse_on = None
            self._pulse_off = None
            self._ended = True
            clock.schedule(self.leave)
            clock.schedule(self.finalize)

    def _pulse_off_callback(self):
        # turn off the code
        if self._sync_style == "parallel":
            start_time = clock.now()
            self._sport.setData(0)
            end_time = clock.now()
        else:
            start_time = clock.now()
            self._sport.setData("0")
            end_time = clock.now()
        # clean up / close the port
        self._sport = None

        # set the pulse time
        time_err = (end_time - start_time)/2.
        self._pulse_off = event_time(start_time+time_err,
                                     time_err)

        # let's schedule finalizing
        self._ended = True
        clock.schedule(self.finalize)


@Subroutine
def JitteredPulses(self, code=1, width=0.010, port=0,
                   pause_between=3.0, jitter_between=3.0,
                   sync_style="parallel"):
    """Send pulses separated by a jittered wait.

    The typical use case for this subroutine is to send a random train
    of pulses during an EEG experiment to allow for subsequent
    synchronization of the EEG data with the behavioral data. This
    would be accomplished by calling JitteredPulses within a Meanwhile
    as the next state following the instantiation of the Experiment:

    exp = Experiment()
    with Meanwhile():
        JitteredPulses()

    """
    # loop indefinitely
    with Loop():
        # send a pulse
        pulse = Pulse(code=code, port=port, width=width, sync_style=sync_style)
        Done(pulse)

        # do a jittered wait
        Wait(duration=pause_between,
             jitter=jitter_between)

        # Log the pulse to a pulse-specific log
        Log(name='pulse',
            pulse_on=pulse.pulse_on,
            pulse_code=pulse.code,
            pulse_off=pulse.pulse_off,
            pulse_port=pulse.port,
            pulse_width=pulse.width)


if __name__ == '__main__':
    from .experiment import Experiment
    from .state import Meanwhile, Debug

    # set up default experiment
    exp = Experiment()

    # test running pulses whilst the rest of the experiment is going
    with Meanwhile():
        with Loop():
            pulse = Pulse(code='S1')
            Wait(duration=1.0, jitter=1.0)
            Log(name='pulse',
                pulse_on=pulse.pulse_on,
                pulse_code=pulse.code,
                pulse_off=pulse.pulse_off)

    # First wait for a bit and send some pulses
    Wait(10)

    # print something
    Debug(width=exp.screen.width, height=exp.screen.height)

    # run the exp
    exp.run(trace=False)
