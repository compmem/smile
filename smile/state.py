#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from __future__ import with_statement
from pyglet import clock

# # get the last instance of the experiment class
# from .experiment import Experiment
# exp = Experiment.last_instance
#from experiment import Experiment

# custom schedule functions
def _schedule_interval_callback(dt, func, interval, *args, **kwargs):
    # schedule it
    if interval > 0:
        clock.schedule_interval(func, interval, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)
def schedule_delayed_interval(func, delay, interval, *args, **kwargs):
    clock.schedule_once(_schedule_interval_callback, delay, func, interval, *args, **kwargs)
    
def _schedule_callback(dt, func, *args, **kwargs):
    # schedule it
    clock.schedule(func, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)
def schedule_delayed(func, delay, *args, **kwargs):
    clock.schedule_once(_schedule_callback, delay, func, *args, **kwargs)

class State(object):
    def __init__(self, interval=0, parent=None, duration=0.0, reset_clock=False):
        self.state_time = None
        self.interval = interval
        self.duration = duration
        self.parent = parent
        self.reset_clock = reset_clock
        self.reset_next = False
        self.active = False
        self.done = False
        if self.parent:
            # append to children
            self.parent.children.append(self)

    def _callback(self, dt):
        pass
        
    def callback(self, dt):
        # call the user-defined callback
        self._callback(dt)
        if self.interval == 0:
            # we're done
            self.leave()

    def get_parent_state_time(self):
        if not self.reset_clock and self.parent:
            return self.parent.get_state_time()
        else:
            return clock._default.time()

    def advance_parent_state_time(self, duration):
        if self.parent:
            self.parent.advance_state_time(duration)

    def _enter(self):
        pass

    def enter(self):
        # get the starting time from the parent
        self.state_time = self.get_parent_state_time()

        # add the callback to the schedule
        delay = self.state_time - clock._default.time()
        if delay < 0:
            delay = 0
        if self.interval < 0:
            # schedule it for every frame
            schedule_delayed(self.callback, delay)
        else:
            # schedule the interval (0 means once)
            schedule_delayed_interval(self.callback, delay, self.interval)

        # say we're active
        self.active = True

        # update the parent time if necessary
        if self.duration > 0:
            self.advance_parent_state_time(self.duration)

        # custom enter code
        self._enter()

        pass

    def _leave(self):
        pass

    def leave(self):
        # update the parent state time to actual elapsed time if necessary
        if self.duration < 0:
            self.advance_parent_state_time(clock._default.time()-self.state_time)

        # remove the callback from the schedule
        clock.unschedule(self.callback)

        # notify the parent that we're done
        self.active = False
        self.done = True
        if self.parent:
            self.parent.check = True

        # call custom leave code
        self._leave()

        pass
    


class ParentState(State):
    def __init__(self, parent=None, duration=-1, reset_clock=False):
        super(ParentState, self).__init__(interval=-1, parent=parent, 
                                          duration=duration, reset_clock=reset_clock)
        self.children = []
        self.check = True

    def get_state_time(self):
        return self.state_time

    def advance_state_time(self, duration):
        self.state_time += duration

    def _enter(self):
        # set all children to not done
        for c in self.children:
            c.done = False

    def __enter__(self):
        # push self as current parent
        #Experiment.last_instance._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        #state = Experiment.last_instance._parents.pop()
        pass

class Parallel(ParentState):
    """
    A Parallel State is done when all its children have finished.
    """        
    def _callback(self, dt):
        if self.check:
            # process the children
            # start those that are not active and not done
            num_done = 0
            for c in self.children:
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    c.enter()
            if num_done == len(self.children):
                # we're done
                self.interval = 0
        pass

    def advance_state_time(self, duration):
        # we don't advance state time in parallel parents
        pass


class Serial(ParentState):
    """
    A Serial State is done when the last state in the chain is finished.
    """
    def _callback(self, dt):
        if self.check:
            # process the children
            # start those that are not active and not done
            reset_next = False
            num_done = 0
            for i,c in enumerate(self.children):
                if c.done:
                    num_done += 1
                    # set whether we should reset the next
                    reset_next = c.reset_next
                    continue
                if not c.active:
                    if i > 0 and \
                            not self.children[i-1].done and \
                            self.children[i-1].duration < 0:
                        # we have to wait until it's done
                        break

                    # start the next one
                    if reset_next:
                        c.reset_clock = True
                    c.enter()
                    break

                # set whether we should reset the next
                reset_next = c.reset_next

            if num_done == len(self.children):
                # we're done
                self.interval = 0
        pass

class Conditional(ParentState):
    """
    Parent state to implement branching.
    """
    pass

class Wait(State):
    def __init__(self, duration=0.0, stay_active=False, 
                 interval=0, parent=None, reset_clock=False):
        # init the parent class
        super(Wait, self).__init__(interval=-1, parent=parent, 
                                   duration=duration, reset_clock=reset_clock)
        self.stay_active = stay_active

    def _callback(self, dt):
        if not self.stay_active or clock._default.time() >= self.state_time+self.duration:
            # we're done
            self.interval = 0
    

class Func(State):
    def __init__(self, func, args=None, kwargs=None, 
                 interval=0, parent=None, duration=0.0, reset_clock=False):
        # init the parent class
        super(Func, self).__init__(interval=interval, parent=parent, 
                                   duration=duration, reset_clock=reset_clock)

        # set up the state
        self.func = func
        self.args = args
        if self.args is None:
            self.args = []
        self.kwargs = kwargs
        if self.kwargs is None:
            self.kwargs = {}

    def _callback(self, dt):
        self.dt = dt
        self.res = self.func(self, *self.args, **self.kwargs)
        if self.interval == 0:
            # we're done
            self.leave()

if __name__ == '__main__':

    from experiment import Experiment

    def print_dt(state, txt):
        print txt, clock._default.time(), state.state_time, state.dt

    exp = Experiment()
    Func(print_dt, args=["one"], interval=0.0, parent=exp)
    Wait(2.0, parent=exp)
    Func(print_dt, args=["two"], interval=0.0, parent=exp)
    Wait(3.0, parent=exp)
    with Parallel(parent=exp) as trial:
        with Serial(parent=trial) as x:
            Wait(1.0, parent=x)
            Func(print_dt, args=['three'], interval=0.0, parent=x)
        Func(print_dt, args=['four'], interval=0.0, parent=trial)
        print trial.children
    Wait(2.0, stay_active=True, parent=exp)

    exp.run()

    
    pass

