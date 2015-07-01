import sys

if any([name.startswith("kivy") for name in sys.modules.keys() if
        name != "kivy_overrides"]):
    raise ImportError("smile must be imported before kivy")
import kivy
EXACT_KIVY_VERSION = "1.8.0"
if kivy.__version__ != EXACT_KIVY_VERSION:
    raise ImportError("kivy version must be exactly %r, got %r" %
                      (EXACT_KIVY_VERSION, kivy.__version__))
import kivy.base
class SmileEventLoop(kivy.base.EventLoopBase):
    def __init__(self):
        super(SmileEventLoop, self).__init__()
        self._idle_callback = None
    def set_idle_callback(self, callback):
        self._idle_callback = callback
    def idle(self):
        if self._idle_callback:
            self._idle_callback(self)
        
        # don't loop if we don't have listeners !
        if len(self.event_listeners) == 0:
            Logger.error('Base: No event listeners have been created')
            Logger.error('Base: Application will leave')
            self.exit()
            return False

        return self.quit
kivy.base.EventLoop = SmileEventLoop()
#import kivy.clock
#kivy.clock.ClockBase.MIN_SLEEP = 0.0
#kivy.clock.ClockBase.SLEEP_UNDERSHOOT = 0.0
#kivy.clock.Clock._max_fps = 2000.0
