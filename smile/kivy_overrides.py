import sys

if any([name.startswith("kivy") for name in sys.modules.keys() if
        name != "kivy_overrides"]):
    raise ImportError("smile must be imported before kivy")

# Prevent kivy from reading command line options...
sys_argv = sys.argv[1:]
sys.argv = sys.argv[:1]

from kivy.config import Config
Config.set("kivy", "exit_on_escape", 0)
Config.set("kivy", "desktop", 1)
Config.set("graphics", "maxfps", 0)
Config.set("graphics", "fullscreen", "auto")
#Config.set("graphics", "fullscreen", True)
Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set('graphics', 'show_cursor', 0)
Config.set('graphics', 'resizable', 0)
import kivy
EXACT_KIVY_VERSIONS = (
    "1.8.0",
    "1.9.0")
if kivy.__version__ not in EXACT_KIVY_VERSIONS:
    raise ImportError("kivy version must be one of %r, got %r" %
                      (EXACT_KIVY_VERSIONS, kivy.__version__))
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
