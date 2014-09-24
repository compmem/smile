#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from pyglet import clock
now = clock._default.time
import random

from ref import Ref, val
from utils import rindex, get_class_name
from log import dump

# custom schedule functions (add delays)
def _schedule_interval_callback(dt, func, interval, *args, **kwargs):
    """
    Schedule a callback with specified interval.
    """
    # schedule it
    if interval > 0:
        clock.schedule_interval(func, interval, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)
def schedule_delayed_interval(func, delay, interval, *args, **kwargs):
    """
    Schedule a callback with specified interval to begin after the
    specified delay.
    """
    clock.schedule_once(_schedule_interval_callback, delay, func, interval, *args, **kwargs)
    
def _schedule_callback(dt, func, *args, **kwargs):
    """
    Schedule a callback to occur every event loop.
    """
    # schedule it
    clock.schedule(func, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)
def schedule_delayed(func, delay, *args, **kwargs):
    """
    Schedule a callback to occur every event loop after the specified
    initial delay.
    """
    clock.schedule_once(_schedule_callback, delay, func, *args, **kwargs)


class RunOnEnter():
    """Inherited class to indicate to a state that it should run
    immediately upon entering the state (instead of waiting until the
    state time specified by the parent). This ensures that parent
    states do not disturb the timing their children.
    """
    pass


class State(object):
    """
    Base State object for the hierarchical state machine.

    Provides framework for entering, processing, and leaving states.

    Subclasses can customize behavior by implementing the _enter,
    _callback, and _leave methods.

    Parameters
    ----------
    interval : {0, -1, float}
        The number of seconds between each call.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    duration : {0.0, float}
        Duration of the state.
    save_log : bool
        Whether the state logs itself.
    
    """
    def __init__(self, interval=0, parent=None, duration=0.0, 
                 save_log=True):
        """
        interval of 0 means once, -1 means every frame.
        """
        self.state_time = None
        self.start_time = None
        self.end_time = None
        self.first_call_time = None
        self.first_call_error = None
        self.last_call_time = None
        self.last_call_error = None
        self.dt = None
        self.interval = interval
        self.duration = duration
        self.parent = parent
        self.active = False
        self.done = False
        self.save_log = save_log

        # get the exp reference
        from experiment import Experiment
        try:
            self.exp = Experiment.last_instance()
        except AttributeError:
            self.exp = None

        # try and set the current parent
        if self.parent is None and not self.exp is None:
            # try and get it from the exp
            self.parent = self.exp._parents[-1]

        # add self to children if we have a parent
        if self.parent:
            # append to children
            self.parent.children.append(self)

        # start the log
        self.state = self.__class__.__name__
        self.log_attrs = ['state','state_time','start_time','end_time',
                          'first_call_time','first_call_error',
                          'last_call_time','last_call_error',
                          'duration']

    def get_log(self):
        keyvals = [(a,val(getattr(self,a))) if hasattr(self,a) 
                   else (a,None) for a in self.log_attrs]
        return dict(keyvals)

    def get_log_stream(self):
        if self.exp is None:
            return None
        else:
            return self.exp.state_log_stream
        
    def __getitem__(self, index):
        if hasattr(self, index):
            return Ref(self, index)
        else:
            class_name = get_class_name(self)[0]
            raise ValueError('%s state does not have attribute "%s".' % 
                             (class_name, index))

    # PBS: Must eventually check for specific attrs for this to work
    #def __getattribute__(self, name):
    #    return Ref(self, name)

    def _callback(self, dt):
        pass
        
    def callback(self, dt):
        # log when we've entered the callback the first time
        self.last_call_time = now()
        self.last_call_error = self.last_call_time - self.state_time
        if self.first_call_time is None:
            self.first_call_time = self.last_call_time
            self.first_call_error = self.last_call_error

        # call the user-defined callback
        self._callback(dt)

        # save the dt
        self.dt = dt

        # see if done (check to make sure we didn't already call leave)
        if not self.done and self.interval == 0:
            # we're done
            self.leave()

    def get_parent_state_time(self):
        if self.parent:
            return self.parent.get_state_time()
        else:
            return now()

    def advance_parent_state_time(self, duration):
        if self.parent:
            self.parent.advance_state_time(duration)

    def _enter(self):
        pass

    def enter(self):
        # get the starting time from the parent
        self.state_time = self.get_parent_state_time()
        self.start_time = self.state_time

        # add the callback to the schedule
        delay = self.state_time - now()
        if delay < 0 or issubclass(self.__class__,RunOnEnter):
            # parents states (and states like Logging) run immediately
            delay = 0
        if self.interval < 0:
            # schedule it for every event loop
            schedule_delayed(self.callback, delay)
        else:
            # schedule the interval (0 means once)
            schedule_delayed_interval(self.callback, delay, self.interval)

        # say we're active
        self.active = True

        # if we don't have the exp reference, get it now
        if self.exp is None:
            from experiment import Experiment
            self.exp = Experiment.last_instance()
            
        # custom enter code
        self._enter()

        # update the parent time if necessary
        # moved to after _enter in case we update duration
        if self.duration > 0:
            self.advance_parent_state_time(self.duration)

        pass

    def _leave(self):
        pass

    def leave(self):
        # get the end time
        self.end_time = now()
        
        # update the parent state time to actual elapsed time if necessary
        if self.duration < 0:
            if issubclass(self.__class__,ParentState): #isinstance(self, ParentState):
                # advance the duration the children moved the this parent
                duration = self.state_time-self.start_time
            else:
                # advance the duration of this state
                duration = self.end_time-self.start_time
            self.advance_parent_state_time(duration)

        # remove the callback from the schedule
        clock.unschedule(self.callback)

        # notify the parent that we're done
        self.active = False
        self.done = True
        if self.parent:
            self.parent.check = True

        # call custom leave code
        self._leave()

        # write log to the state log
        #print self.get_log()
        if self.save_log:
            dump([self.get_log()],self.get_log_stream())
        pass
    

class ParentState(State, RunOnEnter):
    """Base state for parents that can hold children states. 

    Only parent states can contain other states.

    Implicit hierarchies can be generated using the `with` syntax.

    """
    def __init__(self, children=None, parent=None, duration=-1, save_log=True):
        super(ParentState, self).__init__(interval=-1, parent=parent, 
                                          duration=duration, 
                                          save_log=save_log)
        # process children
        if children is None:
            children = []
        self.children = []
        for c in children:
            self.claim_child(c)
        
        self.check = False

    def get_state_time(self):
        return self.state_time

    def advance_state_time(self, duration):
        self.state_time += duration

    def claim_child(self, child):
        if not child.parent is None:
            ind = rindex(child.parent.children,child)
            del child.parent.children[ind]
        child.parent = self
        self.children.append(child)

    def _enter(self):
        # set all children to not done
        for c in self.children:
            c.done = False
        self.check = True
        self._advanced = 0 # for Parallel children

    def __enter__(self):
        # push self as current parent
        if not self.exp is None:
            self.exp._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        # pop self off
        if not self.exp is None:
            state = self.exp._parents.pop()
        pass


class Parallel(ParentState):
    """Parent state that runs its children in parallel.

    A Parallel Parent State is done when all its children have
    finished.

    """        
    def _callback(self, dt):
        if self.check:
            self.check = False
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
                #self.interval = 0
                # advance the state_time
                self.state_time += self._advanced
                self.leave()
        pass

    def advance_state_time(self, duration):
        # advance the longest duration
        to_advance = duration - self._advanced
        if to_advance > 0:
            #self.state_time += to_advance
            self._advanced += to_advance


class Serial(ParentState):
    """Parent state that runs its children in serial.

    A Serial Parent State is done when the last state in the chain is
    finished.
    """
    def _callback(self, dt):
        if self.check:
            self.check = False
            # process the children
            # start those that are not active and not done
            num_done = 0
            for i,c in enumerate(self.children):
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    if i > 0 and \
                            not self.children[i-1].done and \
                            self.children[i-1].duration < 0:
                        # we have to wait until it's done
                        break

                    # start the next one
                    c.enter()
                    break

            if num_done == len(self.children):
                # we're done
                #self.interval = 0
                self.leave()
        pass

    
class If(ParentState):
    """
    Parent state to implement conditional branching.

    key = KeyResponse(['Y','N'])
    If((key['rt']>2.0)&(key['resp'] != None), stateA, stateB)

    True and false states are created if they are not
    passed in.  That way we can do

    with If((key['rt']>2.0)&(key['resp'] != None)) as if_state:
        with if_state.true_state:
            # fill the true state
            pass
        with if_state.false_state:
            # fill the false state
            pass

    """
    def __init__(self, conditional, true_state=None, false_state=None, 
                 parent=None, save_log=True):

        # init the parent class
        super(If, self).__init__(parent=parent, duration=-1, 
                                 save_log=save_log)

        # save the cond
        self.cond = conditional
        self.outcome = None
        self.true_state = true_state
        self.false_state = false_state

        if self.true_state:
            # make sure to set this as the parent of the true state
            self.claim_child(self.true_state)
        else:
            # create the true state
            self.true_state = Serial(parent=self)

        # process the false state similarly
        if self.false_state:
            self.claim_child(self.false_state)
        else:
            # create the true state
            self.false_state = Serial(parent=self)

        # append outcome to log
        self.log_attrs.append('outcome')
        
    def _enter(self):
        # reset outcome so we re-evaluate if called in loop
        self.outcome = val(self.cond)
        super(If, self)._enter()
        
    def _callback(self, dt):
        if self.check:
            self.check = False
            done = False

            # process the outcome
            if self.outcome:
                # get the first state
                c = self.true_state
            else:
                c = self.false_state

            if c is None or c.done:
                done = True
            elif not c.active:
                # start the winning state
                c.enter()

            # check if done
            if done:
                #self.interval = 0
                self.leave()

                
class Loop(Serial):
    """
    State that can loop over an iterable or run repeatedly while
    a conditional evaluates to True.
    
    with Loop(block) as trial:
        Show(Image(trial.current['image']), 2.0)
        Wait(.5)
    """
    def __init__(self, iterable=None, conditional=True, 
                 parent=None, save_log=True):
        super(Loop, self).__init__(parent=parent, duration=-1, 
                                   save_log=save_log)

        # otherwise, assume it's a list of dicts
        self.iterable = iterable
        self.cond = conditional
        self.outcome = True

        # set to first in loop
        self.i = 0
                    
        # append outcome to log
        self.log_attrs.extend(['outcome','i'])

    @property
    def current(self):
        if self.iterable is None:
            return None
        else:
            return self['iterable'][self['i']]

    def _enter(self):
        # get the parent enter
        super(Loop, self)._enter()

        # reset outcome so we re-evaluate if called in loop
        self.outcome = val(self.cond)

    def _callback(self, dt):
        if self.check:
            self.check = False
            # check the outcome each time
            if not self.outcome:
                # we should stop now
                #self.interval = 0
                self.leave()
                return
                
            # process the children            
            # start those that are not active and not done
            num_done = 0
            for i,c in enumerate(self.children):
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    if i > 0 and \
                            not self.children[i-1].done and \
                            self.children[i-1].duration < 0:
                        # we have to wait until it's done
                        break

                    # start the next one
                    c.enter()
                    break

            if num_done == len(self.children):
                # we're done with this sequence
                finished = False
                if not self.iterable is None:
                    # see if we're done with the loop
                    if self.i+1 >= len(val(self.iterable,recurse=False)):
                        # we're really done
                        finished = True
                        self.leave()
                        # reset to start if inside another loop
                        self.i = 0
                    else:
                        # dump log
                        dump([self.get_log()],self.get_log_stream())

                        # set to next
                        self.i += 1
                        
                # update everything for the next loop
                if not finished:
                    self._enter()
                    
        pass


class Wait(State):
    """
    State that will wait a specified time in seconds.  It is possible
    to keep the state active or simply move the parent's state time
    ahead.
    """
    def __init__(self, duration=0.0, jitter=0.0, stay_active=False, 
                 parent=None, save_log=True):
        # init the parent class
        super(Wait, self).__init__(interval=-1, parent=parent, 
                                   duration=duration, 
                                   save_log=save_log)
        self.stay_active = stay_active
        self.jitter = jitter
        self.wait_duration = duration

    def _enter(self):
        # get the parent enter
        super(Wait, self)._enter()

        # set the duration
        self.duration = random.uniform(val(self.wait_duration),
                                       val(self.wait_duration)+val(self.jitter))

    def _callback(self, dt):
        if not self.stay_active or now() >= self.state_time+self.duration:
            # we're done
            #self.interval = 0
            self.leave()


class ResetClock(State, RunOnEnter):
    """
    State that will reset the clock of its parent to a specific time
    (or now if not specified).
    """
    def __init__(self, new_time=None, parent=None, save_log=True):
        # init the parent class
        super(ResetClock, self).__init__(interval=0, parent=parent, 
                                         duration=0, 
                                         save_log=save_log)
        if new_time is None:
            # eval to now if nothing specified
            new_time = Ref(gfunc=lambda:now())
        self.new_time = new_time

    def _callback(self, dt):
        duration = val(self.new_time) - self.get_parent_state_time()
        if duration > 0:
            self.advance_parent_state_time(duration)
    

class Func(State):
    """
    State that will call a Python function, passing this state as the
    first argument.
    """
    def __init__(self, func, args=None, kwargs=None, 
                 interval=0, parent=None, duration=0.0, 
                 save_log=True):
        # init the parent class
        super(Func, self).__init__(interval=interval, parent=parent, 
                                   duration=duration, 
                                   save_log=save_log)

        # set up the state
        self.func = func
        self.args = args
        if self.args is None:
            self.args = []
        self.kwargs = kwargs
        if self.kwargs is None:
            self.kwargs = {}

    def _callback(self, dt):
        # process the refs
        args = val(self.args)
        kwargs = val(self.kwargs)
        self.res = self.func(self, *args, **kwargs)
    

class Debug(State):
    """
    State that will evaluate the specified kwargs and print them to standard out for debugging purposes.
    """
    def __init__(self, parent=None, save_log=False, **kwargs):
        # init the parent class
        super(Debug, self).__init__(interval=0, parent=parent, 
                                   duration=0, 
                                   save_log=save_log)

        # set up the state
        self.kwargs = kwargs

    def _callback(self, dt):
        # process the refs
        #kwargs = {key: val(value) for (key, value) in self.kwargs}
        print 'DEBUG:', val(self.kwargs)


if __name__ == '__main__':

    from experiment import Experiment

    def print_dt(state, *txt):
        print txt, now()-state.state_time, state.dt

    exp = Experiment()

    Debug(width=exp['window'].width, height=exp['window'].height)

    # with implied parents
    block = [{'val':i} for i in range(3)]
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current['val']])
        Wait(1.0)
        If(trial.current['val']==block[-1],
           Wait(2.))

    block = range(3)
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current])
        Wait(1.0)
        If(trial.current==block[-1],
           Wait(2.))


    If(True, 
       Func(print_dt, args=["True"]),
       Func(print_dt, args=["False"]))
    Wait(1.0)
    If(False, 
       Func(print_dt, args=["True"]),
       Func(print_dt, args=["False"]))
    Wait(2.0)
    If(False, Func(print_dt, args=["True"])) # won't do anything
    Func(print_dt, args=["two"])
    Wait(3.0)
    with Parallel():
        with Serial():
            Wait(1.0)
            Func(print_dt, args=['three'])
        Func(print_dt, args=['four'])
    Wait(2.0)

    block = [{'text':'a'},{'text':'b'},{'text':'c'}]
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current['text']])
        Wait(1.0)
        
    Wait(2.0, stay_active=True)

    exp.run()


    # # with explicit parents
    # If(True, 
    #    Func(print_dt, args=["True"], interval=0.0),
    #    Func(print_dt, args=["False"], interval=0.0),
    #    parent=exp)
    # Wait(1.0, parent=exp)
    # If(False, 
    #    Func(print_dt, args=["True"], interval=0.0),
    #    Func(print_dt, args=["False"], interval=0.0),
    #    parent=exp)
    # Wait(2.0, parent=exp)
    # Func(print_dt, args=["two"], interval=0.0, parent=exp)
    # Wait(3.0, parent=exp)
    # with Parallel(parent=exp) as trial:
    #     with Serial(parent=trial) as x:
    #         Wait(1.0, parent=x)
    #         Func(print_dt, args=['three'], interval=0.0, parent=x)
    #     Func(print_dt, args=['four'], interval=0.0, parent=trial)
    #     print trial.children
    # Wait(2.0, stay_active=True, parent=exp)

    
    pass

