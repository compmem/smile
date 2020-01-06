#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
#   NOTES: On Demand timing, the default, makes it so that the write() method
#   doesn't return until all of the samples are written. This also means that
#   we can get it to send different kinds of signals.
#
#   PLAN: enter is a write to VCC, Leave is a write to 0. Channel is designated
#   by the state parameters. tasks must be setup before hand and passed into
#   the state much like the servers.
#
#   NOTE: We are calculating the timing of a NI Pulse based on when the call
#   to write returns. This is due to the fack that write will block until the
#   value in the NIUSB is updated.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .state import State
from .event import event_time
from .clock import clock
from .ref import NotAvailable

try:
    from nidaqmx.task import Task
    _got_nidaqmx = True
except ImportError:
    print("Unable to import nidaqmx!")
    _got_nidaqmx = False


_ni_tasks = {}


def init_task(task_name="ttl_pulse", min_val=0.0, max_val=1.0,
              chan_path='Dev1/ao0', chan_des="mychan"):
    if _got_nidaqmx:
        global _ni_tasks

        if task_name in _ni_tasks.keys():
            return _ni_tasks[task_name]
        else:
            _ni_tasks[task_name] = Task(task_name)
            _ni_tasks[task_name].ao_channels.add_ao_voltage_chan(chan_path,
                                                                 chan_des,
                                                                 min_val,
                                                                 max_val)
            return _ni_tasks[task_name]
    else:
        print("Unable to setup ni Task! No sync pulses will be made.")
        return None


class NIPulse(State):
    def __init__(self, task, push_vals=[1.0], width=0.010, **kwargs):
        # init the parent class
        super(NIPulse, self).__init__(parent=kwargs.pop("parent", None),
                                      duration=kwargs.pop("duration", 0.0),
                                      save_log=kwargs.pop("save_log", True),
                                      name=kwargs.pop("name", None),
                                      blocking=kwargs.pop("blocking", True))
        # handle the values that could require initialization
        self._init_task = task
        self._init_push_vals = push_vals
        self._init_width = width
        self._pulse_on = NotAvailable
        self._pulse_off = NotAvailable

        self._log_attrs.extend(['push_vals', 'pulse_on', 'pulse_off', 'width'])

    def _schedule_start(self):
        clock.schedule(self._callback, event_time=self._start_time)

    def _unschedule_start(self):
        clock.unschedule(self._callback)

    def _callback(self):
        # we've started
        self._started = True

        # push it outlet
        global _got_nidaqmx
        if _got_nidaqmx:
            if type(self._push_vals == list):
                self._task.write(self._push_vals)
            else:
                self._task.write([self.push_vals])
            ev = clock.now()

        else:
            self._pulse_on = None
            self._pulse_off = None
            self._ended = True
            clock.schedule(self.leave)
            clock.schedule(self.finalize)
            return

        # set the pulse time
        self._pulse_on = event_time(ev,
                                    0.0)

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

            # so we can finalize now, too
            clock.schedule(self.finalize)
            self._ended = True

    def _pulse_off_callback(self):
        self._task.write([0.0])
        ev = clock.now()

        # set the pulse time
        self._pulse_off = event_time(ev,
                                     0.0)

        # let's schedule finalizing
        self._ended = True
        clock.schedule(self.finalize)
