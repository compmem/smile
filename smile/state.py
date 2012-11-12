#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

#from __future__ import with_statement
from pyglet import clock
now = clock._default.time

from ref import Ref, val
from utils import rindex

# # get the last instance of the experiment class
# from .experiment import Experiment
# exp = Experiment.last_instance
#from experiment import Experiment

# custom schedule functions (add delays)
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

_global_parents = []

class State(object):
    def __init__(self, interval=0, parent=None, duration=0.0, reset_clock=False):
        self.state_time = None
        self.start_time = None
        self.interval = interval
        self.duration = duration
        self.parent = parent
        self.reset_clock = reset_clock
        self.reset_next = False
        self.active = False
        self.done = False

        # get the exp reference
        from experiment import Experiment
        try:
            self.exp = Experiment.last_instance()
        except AttributeError:
            self.exp = None

        #if self.parent is None and len(_global_parents) > 0: #not self.exp is None:
        if self.parent is None and not self.exp is None:
            # try and get it from the exp
            self.parent = self.exp._parents[-1]
            #self.parent = _global_parents[-1]

        # add self to children if we have a parent
        if self.parent:
            # append to children
            self.parent.children.append(self)
        self.log = {'state':self.__class__.__name__}

    def __getitem__(self, index):
        return Ref(self, index)

    def _callback(self, dt):
        pass
        
    def callback(self, dt):
        # log when we've entered the callback the first time
        if not self.log.has_key('first_call_time'):
            self.log['first_call_time'] = now()

        # call the user-defined callback
        self._callback(dt)

        # see if done
        if self.interval == 0:
            # we're done
            self.leave()

    def get_parent_state_time(self):
        if not self.reset_clock and self.parent:
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

        # save the starting state time
        self.log['start_time'] = self.start_time

        # add the callback to the schedule
        delay = self.state_time - now()
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
            if isinstance(self, ParentState):
                self.advance_parent_state_time(self.state_time-self.start_time)
            else:
                self.advance_parent_state_time(now()-self.start_time)

        # remove the callback from the schedule
        clock.unschedule(self.callback)

        # notify the parent that we're done
        self.active = False
        self.done = True
        if self.parent:
            self.parent.check = True

        # call custom leave code
        self._leave()

        #print self.log
        pass
    


class ParentState(State):
    def __init__(self, parent=None, duration=-1, reset_clock=False):
        super(ParentState, self).__init__(interval=-1, parent=parent, 
                                          duration=duration, reset_clock=reset_clock)
        self.children = []

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

    def __enter__(self):
        # push self as current parent
        # global _global_parents
        # if len(_global_parents) > 0:
        #     _global_parents.append(self)
        if not self.exp is None:
            self.exp._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        # pop self off
        # global _global_parents
        # if len(_global_parents) > 0:
        #     state = _global_parents.pop()
        if not self.exp is None:
            state = self.exp._parents.pop()
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
                # if any of the children ask to reset next, self should too
                if c.reset_next:
                    self.reset_next = True
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
                # if any of the children ask to reset next, self should too
                if c.reset_next:
                    self.reset_next = True
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

    
class If(ParentState):
    """
    Parent state to implement branching.

    key = KeyResponse(['Y','N'])
    If((key['rt']>2.0)&(key['resp'] != None), stateA, stateB)

    When()

    The issue is that key['rt'] must be evaluated when IfElse is entered.
    """
    def __init__(self, conditional, true_state, false_state=None, 
                 parent=None, reset_clock=False):

        # init the parent class
        super(If, self).__init__(parent=parent, duration=-1, 
                                 reset_clock=reset_clock)

        # save the cond
        self.cond = conditional
        self.outcome = None
        self.true_state = true_state
        self.false_state = false_state

        # make sure to set this as the parent of the true state
        self.claim_child(self.true_state)

        # process the false state similarly
        if self.false_state:
            self.claim_child(self.false_state)

    def _enter(self):
        # reset outcome so we re-evaluate if called in loop
        self.outcome = val(self.cond)
        super(If, self)._enter()
        
    def _callback(self, dt):
        if self.check:
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
                self.interval = 0

class LoopItem(object):
    def __init__(self, item):
        self.item = item
        self.value = Ref(self,'item')
        
    def __getitem__(self, index):
        # modify so that we're accessing item
        return Ref(gfunc = lambda : self.item[index])
        
class Loop(Serial):
    """
    with Loop(block) as trial:
        Show(Image(trial.current['image']), 2.0)
        Wait(.5)
    """
    def __init__(self, iterable=None, conditional=True, 
                 parent=None, reset_clock=False):
        super(Loop, self).__init__(parent=parent, duration=-1, 
                                   reset_clock=reset_clock)

        # otherwise, assume it's a list of dicts
        self.iterable = iterable
        self.cond = conditional
        self.outcome = True
        
        # set to first in loop
        self.i = 0
        if not self.iterable is None:
            if len(self.iterable) == 0:
                raise ValueError('The iterable can not be zero length.')
            self.current = LoopItem(self.iterable[self.i])
        
    def _enter(self):
        # reset outcome so we re-evaluate if called in loop
        self.outcome = val(self.cond)
        super(Loop, self)._enter()

    def _callback(self, dt):
        if self.check:
            # check the outcome each time
            if not self.outcome:
                # we should stop now
                self.interval = 0
                return
                
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
                # we're done with this sequence
                self.i += 1
                if not self.iterable is None:
                    # see if we're done with the loop
                    if self.i >= len(self.iterable):
                        # we're really done
                        self.interval = 0
                    else:
                        # set to next
                        self.current.item = self.iterable[self.i]

                if self.interval != 0:
                    # reset all the child states and update outcome
                    self._enter()
                    
        pass

        
class Wait(State):
    def __init__(self, duration=0.0, stay_active=False, 
                 parent=None, reset_clock=False):
        # init the parent class
        super(Wait, self).__init__(interval=-1, parent=parent, 
                                   duration=duration, reset_clock=reset_clock)
        self.stay_active = stay_active

    def _callback(self, dt):
        if not self.stay_active or now() >= self.state_time+self.duration:
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
        # process the refs
        args = [val(a) for a in self.args]
        kwargs = {key: val(value) for (key, value) in self.kwargs}
        self.res = self.func(self, *args, **kwargs)

if __name__ == '__main__':

    from experiment import Experiment

    def print_dt(state, *txt):
        print txt, now()-state.state_time, state.dt

    exp = Experiment()

    # with implied parents
    block = range(3)
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current.value])
        Wait(1.0)
        If(trial.current.value==block[-1],
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

