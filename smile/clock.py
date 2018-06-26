import smile.kivy_overrides as kivy_overrides
import kivy.clock

_get_time = kivy.clock._default_time
_kivy_clock = kivy.clock.Clock

class _ClockEvent(object):
    def __init__(self, clock, func, event_time, repeat_interval):
        self.clock = clock
        self.func = func
        self.event_time = event_time
        self.repeat_interval = repeat_interval

class Clock(object):
    def __init__(self):
        self._events = []

    def now(self):
        return _get_time()

    def tick(self):
        #TODO: limit time spent in each tick?
        now = self.now()
        while len(self._events):
            event = self._events[0]
            if event.event_time is None or now >= event.event_time:
                del self._events[0]
                if event.repeat_interval is not None:
                    if event.event_time is None:
                        event.event_time = now + event.repeat_interval
                    else:
                        event.event_time += event.repeat_interval
                    self._schedule(event)
                event.func()
            else:
                break

    def usleep(self, usec):
        _kivy_clock.usleep(usec)

    def _schedule(self, event):
        for n, cmp_event in enumerate(self._events):
            if ((event.event_time is None and
                 cmp_event.event_time is not None) or
                (event.event_time is not None and
                 cmp_event.event_time is not None and
                 event.event_time < cmp_event.event_time)):
                self._events.insert(n, event)
                break
        else:
            self._events.append(event)

    def schedule(self, func, event_delay=None, event_time=None,
                 repeat_interval=None):
        if event_delay is not None:
            event_time = self.now() + event_delay
        self._schedule(_ClockEvent(self, func, event_time, repeat_interval))
        return func

    def unschedule(self, func):
        self._events = [event for event in self._events if event.func != func]

clock = Clock()
