#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# import main modules
#from __future__ import with_statement
import sys
import weakref

# pyglet imports
import pyglet
from pyglet.gl import *
from pyglet import clock
from pyglet.window import key,Window

# local imports
from state import Serial

# set up the basic timer
now = clock._default.time
def event_time(time, time_error=0.0):
    return {'time':time, 'time_error':time_error}
    
class ExpWindow(Window):
    def __init__(self, exp, *args, **kwargs):
        # init the pyglet window
        super(ExpWindow, self).__init__(*args, **kwargs)

        # set up the exp
        self.exp = exp

        # set up easy key logging
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)

        # set empty list of key and mouse handler callbacks
        self.key_callbacks = []
        self.mouse_callbacks = []

        # set up a batch for fast rendering
        # eventually we'll need multiple groups
        self.batch = pyglet.graphics.Batch()

        # say we've got nothing to plot
        self.need_flip = False
        self.need_draw = False

    def on_draw(self, force=False):
        if force or self.need_draw:
            self.clear()
            self.batch.draw()
            self.need_flip = True

    def set_clear_color(self,color=(0,0,0,1)):
        glClearColor(*color)
                
    def on_mouse_motion(self, x, y, dx, dy):
        pass
    def on_mouse_press(self, x, y, button, modifiers):
        pass
        
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.has_exit = True

        # call the registered callbacks
        for c in self.key_callbacks:
            # pass it the key, mod, and event time
            c(symbol, modifiers, self.exp.event_time)

    def on_key_release(self, symbol, modifiers):
        pass

class Experiment(Serial):
    def __init__(self, fullscreen=False, resolution=(800,600), name="Smile",
                 pyglet_vsync=True, background_color=(0,0,0,1)):

        # parse args

        # set up the state
        super(Experiment, self).__init__(parent=None, duration=0)

        # set up the window
        self.pyglet_vsync = pyglet_vsync
        if fullscreen:
            self.window = ExpWindow(self, fullscreen=fullscreen, 
                                    caption=name, vsync=pyglet_vsync)
        else:
            self.window = ExpWindow(self, *resolution,
                                    fullscreen=fullscreen, 
                                    caption=name, vsync=pyglet_vsync)
            
        # set the clear color
        self.window.set_clear_color(background_color)

        # set the mouse as desired
        #self.window.set_exclusive_mouse()

        # some gl stuff (must look up to remember why we want them)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # get a clock for sleeping 
        self.clock = pyglet.clock._default

        # set up instance for access throughout code
        self.__class__.last_instance = weakref.ref(self)

        # init parents (with self at top)
        self._parents = [self]
        #global state._global_parents
        #state._global_parents.append(self)

        # we have not flipped yet
        self.last_flip = event_time(0.0)

        # get flip interval
        self.flip_interval = self._calc_flip_interval()

        # event time
        self.last_event = event_time(0.0)
        
    def run(self, initial_state=None):
        """
        Run the experiment.
        """

        # first clear and do a flip
        #glClear(GL_COLOR_BUFFER_BIT)
        self.window.on_draw(force=True)
        self.blocking_flip()

        # start the first state (that's this experiment)
        self.enter()

        # process events until done
        self._last_time = now()
        while not self.done and not self.window.has_exit:
            # record the time range
            self._new_time = now()
            time_err = (self._new_time - self._last_time)/2.
            self.event_time = event_time(self._last_time+time_err,
                                         time_err)

            # process the events that occurred in that range
            self.window.dispatch_events()

            # handle all scheduled callbacks
            dt = clock.tick(poll=True)

            # put in sleeps if necessary
            if dt < .0001:
                # do a usleep for half a ms (might need to tweak)
                self.clock.sleep(500)

            # save the time
            self._last_time = self._new_time

    def _calc_flip_interval(self, nflips=20, nignore=5):
        """
        Calculate the mean flip interval.
        """
        import random
        diffs = 0.0
        last_time = 0.0
        count = 0.0
        for i in range(nflips):
            # must draw something so the flip happens
            color = (random.uniform(0,1),
                     random.uniform(0,1),
                     random.uniform(0,1),
                     1.0)
            self.window.set_clear_color(color)
            self.window.on_draw(force=True)

            # perform the flip and record the flip interval
            cur_time = self.blocking_flip()
            if last_time > 0.0 and i >= nignore:
                diffs += cur_time['time']-last_time['time']
                count += 1
            last_time = cur_time

            # add in sleep of something definitely less than the refresh rate
            self.clock.sleep(5000)  # 5ms for 200Hz

        # take the mean and return
        return diffs/count

    def blocking_flip(self):
        # only flip if we've drawn
        if self.window.need_flip:
            # first the flip
            self.window.flip()

            if not self.pyglet_vsync:
                # OpenGL:
                glDrawBuffer(GL_BACK)
                # We draw our single pixel with an alpha-value of zero
                # - so effectively it doesn't change the color buffer
                # - just the z-buffer if z-writes are enabled...
                glColor4f(0,0,0,0)
                glBegin(GL_POINTS)
                glVertex2i(10,10)
                glEnd()
                # This glFinish() will wait until point drawing is
                # finished, ergo backbuffer was ready for drawing,
                # ergo buffer swap in sync with start of VBL has
                # happened.
                glFinish()

            # return when it happened
            self.last_flip = event_time(now(),0.0)

            # no need for flip anymore
            self.window.need_flip = False

        return self.last_flip

            
if __name__ == '__main__':
    exp = Experiment(fullscreen=False, pyglet_vsync=False)
    print exp.flip_interval
    exp.run()
    
