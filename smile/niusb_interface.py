#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

#   NOTES: On Demand timing, the default, makes it so that the write() method
#   doesn't return until all of the samples are written. 
#
#   NOTE: We are calculating the timing of a NI Pulse based on when the call
#   to write returns. This is due to the fact that write will block until the
#   value in the NIUSB is updated.
#
# NIDAQMX task inits
# read_licker = Task("ReadFromAi")
# read_licker.ai_channels.add_ai_voltage_chan('Dev1/ai0:2',
#                                             "Licker",
#                                             min_val=0.,
#                                             max_val=0.,)
# write_reward = Task("WriteToAo")
# write_reward.ao_channels.add_ao_voltage_chan('Dev1/ao0:1',
#                                              "rewards",
#                                              min_val=0.0,
#                                              max_val=5.0)
# write_center = Task("WriteToDo")
# write_center.do_channels.add_do_chan('Dev1/port0/line0',
#                                      line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)

from .state import State, CallbackState
from .event import event_time
from .clock import clock
from .ref import NotAvailable

try:
    from nidaqmx.task import Task
    _got_nidaqmx = True
except ImportError:
    print("Unable to import nidaqmx!")
    _got_nidaqmx = False


class NIPulse(State):
    """Send a pulse to analog or digital NI task channels."""
    def __init__(self, task, push_vals=[5.0], width=0.010, **kwargs):
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
        self._task_name = None

        self._log_attrs.extend(['task_name', 'push_vals', 'pulse_on', 
                                'pulse_off', 'width'])

    def _schedule_start(self):
        clock.schedule(self._callback, event_time=self._start_time)

    def _unschedule_start(self):
        clock.unschedule(self._callback)

    def _callback(self):
        # we've started
        self._started = True
        # push it outlet
        if _got_nidaqmx:
            # send the values
            if type(self._push_vals) in (list, tuple):
                self._task.write(self._push_vals)
            else:
                self._task.write([self.push_vals])

            # save the time
            ev = clock.now()
        else:
            self._pulse_on = None
            self._pulse_off = None
            self._ended = True
            clock.schedule(self.leave)
            clock.schedule(self.finalize)
            return

        # set the pulse time
        self._pulse_on = event_time(ev, 0.0)

        # save the task name
        self._task_name = self._task.name

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
        # write to end the pulse
        # must track data type to handle both analog and digital
        if type(self._push_vals) in (list, tuple):
            if type(self._push_vals[0]) is boolean:
                self._task.write([False]*len(self._push_vals))
            else:
                self._task.write([0.0]*len(self._push_vals))
        else:
            if type(self._push_vals) is boolean:
                self._task.write([False])
            else:
                self._task.write([0.0])

        # grab the current time
        ev = clock.now()

        # set the pulse time
        self._pulse_off = event_time(ev, 0.0)

        # stop the task
        self._task.stop()
        
        # let's schedule finalizing
        self._ended = True
        clock.schedule(self.finalize)

        
class NIChangeDetector(CallbackState):
    """Read data via from analog or digital NI Task channels.
    """
    def __init__(self, task, tracked_indices=None, threshold=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None,
                 correct_resp=None, blocking=True):
        # init the parent class
        super(NIChangeDetector, self).__init__(duration=duration, parent=parent,
                                               save_log=save_log, name=name,
                                               blocking=blocking)
        self._init_task = task
        self._task_name = None
        self._init_tracked_indices = tracked_indices
        self._init_threshold = threshold
        self._init_correct_resp = correct_resp
        self._init_base_time = base_time

        self._values = None
        self._changed_channels = None
        self._change_time = None
        self._correct = False
        self._rt = None
        
        # append log vars
        self._log_attrs.extend(['task_name', 'tracked_indices', 'correct_resp',
                                'threshold', 'base_time', 'values',
                                'changed_channels', 'change_time', 'correct',
                                'rt'])

    def _enter(self):
        # call the parent class enter
        super(NIChangeDetector, self)._enter()

        # grab the task name
        self._task_name = self._task.name
        
        # reset defaults
        self._changed_channels = NotAvailable
        self._values = NotAvailable

        self._change_time = NotAvailable
        self._change_time = NotAvailable
        self._rt = NotAvailable
        self._correct = NotAvailable

        if self._tracked_indices is None:
            # pull all from the task channels
            self._tracked_indices = list(range(len(task.ai_channels)))
        if self._base_time is None:
            self._base_time = self._start_time
        if self._threshold is None:
            self._threshold = .01
        if self._correct_resp is None:
            self._correct_resp = []
        elif type(self._correct_resp) not in (list, tuple):
            self._correct_resp = [self._correct_resp]
        
        # start the nidaq
        self._task.start()
        
    def _callback(self):
        # calc trigger
        try:
            # read one sample and don't wait (will error if nothing avail)
            vals = self._task.read(1, 0)

            # grab the time of this read
            ev = clock.now()

            # check if we crossed threshold
            above_thresh_bool = [(vals[y][0]>self._threshold)
                                 for y in self._tracked_indices]
            if any(above_thresh_bool):
                trigger = True
            else:
                trigger = False
        except:
            trigger = False
        
        # evaluate trigger
        if trigger:
            # Test for correct
            # record event time, rt, channels passed threshold, etc
            self._changed_channels = [i for i, t in zip(self._tracked_indices, 
                                                        above_thresh_bool) if t]
            self._values = vals
            
            self._correct = (len(set.intersection(set(self._changed_channels), 
                                                  set(self._correct_resp))) 
                             > 0)
                                 
            self._change_time = event_time(ev, 0.0)
            self._rt = self._change_time['time'] - self._base_time
            
            # let's leave b/c we're all done (use the event time)
            self.cancel(self._change_time['time'])
            return
        else:
            # Schedule this callback again to happen right away
            clock.schedule(self.callback, event_time=clock.now())
    
    def _leave(self):
        # handle the unset variables
        if self._values is NotAvailable:
            self._values = None
        if self._change_time is NotAvailable:
            self._change_time = None
        if self._changed_channels is NotAvailable:
            self._changed_channels = None
        if self._rt is NotAvailable:
            self._rt = None
        if self._correct is NotAvailable:
            self._correct = False

        # stop the task
        self._task.stop()

        # Unschedule callback
        super(NIChangeDetector, self)._leave()

        

