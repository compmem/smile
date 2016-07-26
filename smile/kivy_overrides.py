import sys
import argparse

if "kivy_overrides" not in sys.modules.keys() and \
   any([name.startswith("kivy") for name in sys.modules.keys() if
        name != "kivy_overrides"]):
    raise ImportError("smile must be imported before kivy")

# Prevent kivy from reading command line options...
sys_argv = sys.argv[1:]
sys.argv = sys.argv[:1]

# perform the command line processing
# set up the arg parser
parser = argparse.ArgumentParser(description='Run a SMILE experiment.')
parser.add_argument("-s", "--subject",
                    help="unique subject id",
                    default='test000')
parser.add_argument("-e", "--experiment",
                    help="experiment file",
                    default='')
parser.add_argument("-f", "--fullscreen",
                    help="disable fullscreen",
                    action='store_true')
parser.add_argument("-r", "--resolution",
                    help="screen / window resolution (e.g. '600x800')")
parser.add_argument("-i", "--info",
                    help="additional run info",
                    default='')
parser.add_argument("-c", "--csv",
                    help="perform automatic conversion of SMILE logs to csv",
                    action='store_true')

# do the parsing
args = parser.parse_args(sys_argv)

from kivy.utils import platform

# set kivy config values
from kivy.config import Config
Config.set("kivy", "exit_on_escape", 0)
if platform in ('win', 'linux', 'macosx'):
    Config.set("kivy", "desktop", 1)
else:
    Config.set("kivy", "desktop", 0)

# prevent throttling
Config.set("graphics", "maxfps", 0)

# preload fullscreen
if args.fullscreen:
    # disable fullscreen
    Config.set("graphics", "fullscreen", False)
else:
    Config.set("graphics", "fullscreen", "auto")

# handle resolution
if args.resolution:
    width, height = map(int, args.resolution.split("x"))
    Config.set("graphics", "width", width)
    Config.set("graphics", "height", height)

# prevent right-click multitouch with mouse
Config.set("input", "mouse", "mouse,disable_multitouch")

# hide the cursor (currently doesn't work in 1.9.0, but fixed in 1.9.1)
Config.set('graphics', 'show_cursor', 0)

# we don't want to be able to resize
Config.set('graphics', 'resizable', 0)

# handle supported kivy versions
import kivy
EXACT_KIVY_VERSIONS = (
    "1.8.0",
    "1.9.0",
    "1.9.1-dev0",
    "1.9.1")
if kivy.__version__ not in EXACT_KIVY_VERSIONS:
    raise ImportError("kivy version must be one of %r, got %r" %
                      (EXACT_KIVY_VERSIONS, kivy.__version__))

# provide custom event loop
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
            kivy.base.Logger.error('Base: No event listeners'
                                   ' have been created')
            kivy.base.Logger.error('Base: Application will leave')
            self.exit()
            return False

        return self.quit

kivy.base.EventLoop = SmileEventLoop()
