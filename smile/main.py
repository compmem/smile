# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# import main modules
from __future__ import print_function
import os

# kivy imports
import kivy_overrides
import kivy
import kivy.base
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.base import EventLoop  # this is actually our event loop
from kivy.core.window import Window
from kivy.graphics.opengl import (
    glVertexAttribPointer,
    glVertexAttrib4f,
    glDrawArrays,
    glFinish,
    GL_INT,
    GL_FALSE,
    GL_POINTS)
from kivy.utils import platform
import kivy.clock

# local imports
from event import event_time
from clock import clock
from video import normalize_color_spec


_kivy_clock = kivy.clock.Clock

FLIP_TIME_MARGIN = 0.002     # increase this if we're missing flips
IDLE_USLEEP = 250            # USLEEP During idle


class _VideoChange(object):
    """Container for a change to the graphics tree."""
    def __init__(self, update_cb, flip_time, flip_time_cb):
        self.update_cb = update_cb
        self.flip_time = flip_time
        self.flip_time_cb = flip_time_cb
        self.drawn = False
        self.flipped = False


class SmileApp(App):
    """Kivy app associated with the experiment.

    Not instantiated by the end user."""
    def __init__(self, exp=None):
        super(SmileApp, self).__init__()
        self.exp = exp
        self.callbacks = {}
        self.pending_flip_time = None
        self.video_queue = []
        self.force_blocking_flip = False
        self.force_nonblocking_flip = False
        self.flip_interval = 1/60.  # default to 60 Hz

        # set event_time stuff
        self.event_time = event_time(0., 0.)
        self.dispatch_input_event_time = event_time(0., 0.)

        # make Window avail to exp
        self._Window = Window

    def add_callback(self, event_name, func):
        self.callbacks.setdefault(event_name, []).append(func)

    def remove_callback(self, event_name, event_func):
        try:
            callbacks = self.callbacks[event_name]
        except KeyError:
            return
        self.callbacks[event_name] = [func for func in
                                      self.callbacks[event_name] if
                                      func != event_func]

    def _trigger_callback(self, event_name, *pargs, **kwargs):
        # call the callbacks associated with an event name
        try:
            callbacks = self.callbacks[event_name]
        except KeyError:
            return
        for func in callbacks:
            func(*pargs, **kwargs)

    def build(self):
        # set fullscreen and resolution
        if self.exp._fullscreen is not None:
            Window.fullscreen = self.exp._fullscreen
        if self.exp._resolution is not None:
            Window.system_size = self.exp._resolution

        # handle setting the bg color
        self.set_background_color()

        # base layout uses positional placement
        self.wid = FloatLayout()
        Window._system_keyboard.bind(on_key_down=self._on_key_down,
                                     on_key_up=self._on_key_up)
        Window.bind(on_motion=self._on_motion,
                    mouse_pos=self._on_mouse_pos,
                    on_resize=self._on_resize)
        self.current_touch = None

        # set starting times
        self._post_dispatch_time = clock.now()

        # use our idle callback (defined below)
        kivy.base.EventLoop.set_idle_callback(self._idle_callback)

        # get start of event loop
        EventLoop.bind(on_start=self._on_start)

        # set width and height
        self.exp._screen._set_width(Window.width)
        self.exp._screen._set_height(Window.height)

        return self.wid

    def _on_start(self, *pargs):
        # print "on_start"
        # self.exp._root_state.enter(clock.now() + 1.0)
        self.get_flip_interval()
        self.do_flip(block=True)

        # start the state machine
        self.exp._root_executor.enter(clock.now() + 0.25)

    def _on_resize(self, *pargs):
        # handle the resize
        self.exp._screen._set_width(Window.width)
        self.exp._screen._set_height(Window.height)

        # second half of OSX fullscreen hack that may no longer be needed
        if platform in ('macosx',) and Window.fullscreen and \
           not self.exp._root_executor._enter_time and \
           not self.exp._root_executor._active:
            self.exp._root_executor.enter(clock.now() + 0.25)

        # we need a redraw here
        self.do_flip(block=True)

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[0] == 27 and "shift" in modifiers:
            self.stop()
            return
        name = keycode[1].upper()
        self.exp.screen._keys_down.add(name)
        try:
            self.exp.screen._issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_DOWN", keycode, text, modifiers,
                               self.event_time)

    def _on_key_up(self, keyboard, keycode):
        name = keycode[1].upper()
        self.exp.screen._keys_down.discard(name)
        try:
            self.exp.screen._issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_UP", keycode, self.event_time)

    def _on_mouse_pos(self, window, pos):
        if self.current_touch is None:
            self.exp._screen._set_mouse_pos(tuple(pos))
            self._trigger_callback("MOTION", pos=pos, button=None,
                                   newly_pressed=False,
                                   double=False, triple=False,
                                   event_time=self.event_time)

    def _on_motion(self, window, etype, me):
        if etype == "begin":
            # set the pos
            try:
                w, h = Window._get_effective_size()
            except AttributeError:
                w, h = (Window.width, Window.height)

            me.scale_for_screen(w, h, rotation=Window._rotation,
                                smode=Window.softinput_mode,
                                kheight=Window.keyboard_height)
            self.exp._screen._set_mouse_pos(tuple(int(round(x))
                                                  for x in me.pos))

            # set the button
            try:
                button = me.button
                self.exp._screen._set_mouse_button(button)
            except AttributeError:
                if me.is_touch:
                    # pretend that a touch event is a left button press
                    self.exp._screen._set_mouse_button('left')
                else:
                    self.exp._screen._set_mouse_button(None)
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos,
                                   button=self.exp._screen._mouse_button,
                                   newly_pressed=True,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.dispatch_input_event_time)
        elif etype == "update":
            self.exp._screen._set_mouse_pos(tuple(int(round(x))
                                                  for x in me.pos))
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos,
                                   button=self.exp._screen._mouse_button,
                                   newly_pressed=False,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.dispatch_input_event_time)
        else:
            self.exp._screen._set_mouse_button(None)
            self.exp._screen._set_mouse_pos(tuple(int(round(x))
                                                  for x in me.pos))
            self.current_touch = None
            self._trigger_callback("MOTION", pos=me.pos, button=None,
                                   newly_pressed=False,
                                   double=False, triple=False,
                                   event_time=self.dispatch_input_event_time)

    def _idle_callback(self, event_loop):
        # record the time range
        self._new_time = clock.now()

        # call any of our scheduled events that are ready
        clock.tick()

        # dispatch input events
        time_err = (clock.now() - self._post_dispatch_time) / 2.0
        self.dispatch_input_event_time = event_time(self._post_dispatch_time +
                                                    time_err, time_err)
        event_loop.dispatch_input()
        self._post_dispatch_time = clock.now()

        # processing video and drawing can only happen if we have
        # not already drawn
        if not self._did_draw:
            # prepare for every video to be drawn on the next flip
            for video in self.video_queue:
                # the desired video time must be after the previous flip
                # is done, so making sure the next_flip_time is after
                # ensures this is the case
                if (video.flip_time - self._next_flip_time) < 0.0:

                    if (not video.drawn and
                        ((self.pending_flip_time is None and
                          self._new_time >= (video.flip_time -
                                             (self.flip_interval / 2.0))) or
                         video.flip_time == self.pending_flip_time)):
                        # prepare that video change
                        video.update_cb()

                        # it will be drawn
                        video.drawn = True

                        # save the pending time so all other changes
                        # for that time will also run
                        self.pending_flip_time = video.flip_time
                    else:
                        # either none are ready or the remaining are
                        # for a subsequent flip
                        break
                else:
                    break

            # do kivy ticks and draw when we're ready
            # happens at half the flip interval since last flip
            if clock.now() >= self._next_draw_time:
                # tick the kivy clock
                _kivy_clock.tick()

                # sync Builder and call tick_draw to prepare to draw
                Builder.sync()
                _kivy_clock.tick_draw()
                Builder.sync()
                EventLoop.window.dispatch('on_draw')

                # process smile video callbacks for the upcoming flip
                self._flip_time_callbacks = []
                for video in self.video_queue:
                    if video.drawn and video.flip_time == self.pending_flip_time:
                        # append the flip time callback
                        if video.flip_time_cb is not None:
                            self._flip_time_callbacks.append(video.flip_time_cb)

                        # mark that video as flipped (it's gonna be)
                        video.flipped = True
                    else:
                        # no more of the videos could match, so break
                        break

                # remove any video change that's gonna be flipped
                while len(self.video_queue) and self.video_queue[0].flipped:
                    del self.video_queue[0]

                # we've drawn the one time we can this frame
                self._did_draw = True

        # do a flip when we're ready
        # must have completed draw (this will ensure we don't do double flips
        # inside the FLIP_TIME_MARGIN b/c did_draw will be reset to False upon
        # the flip
        if self._did_draw and \
           clock.now() >= self._next_flip_time-FLIP_TIME_MARGIN:
            # test if blocking or non-blocking flip
            # do a blocking if:
            # 1) Forcing a blocking flip_interval
            #   OR
            # 2) We have a specific flip callback request and we
            #      are not forcing a non-blocking flip
            if self.force_blocking_flip or \
               (len(self._flip_time_callbacks) and
                not self.force_nonblocking_flip):
                # do a blocking flip
                self.do_flip(block=True)
            else:
                # do a non-blocking flip
                self.do_flip(block=False)

            # still may need to update flip_time_callbacks
            # even though they may be wrong for non-blocking flips
            for cb in self._flip_time_callbacks:
                cb(self.last_flip)

            # tell refs that last_flip updated
            self.exp._screen._set_last_flip(self.last_flip)

            # reset for next flip
            self.pending_flip_time = None

        # exit if experiment done
        if not self.exp._root_executor._active:
            if self.exp._root_executor._enter_time:
                # stop if we're not active, but we have an enter time
                self.stop()

        # give time to other threads
        clock.usleep(IDLE_USLEEP)

        # save the time
        self._last_time = clock.now()
        time_err = (self._last_time - self._new_time) / 2.0
        self.event_time = event_time(self._new_time + time_err, time_err)

    def do_flip(self, block=True):
        # call the flip
        EventLoop.window.dispatch('on_flip')

        # TODO: use sync events instead!
        if block:
            # draw a transparent point
            # position
            #@FIX: changed the pointer value to a 0 for testing
            glVertexAttribPointer(0, 2, GL_INT, GL_FALSE, 0,0)
                                  #"\x00\x00\x00\x0a\x00\x00\x00\x0a")
            # color
            glVertexAttrib4f(3, 0.0, 0.0, 0.0, 0.0)
            glDrawArrays(GL_POINTS, 0, 1)

            # wait for flip then point to draw
            glFinish()

            # record the time immediately
            self.last_flip = event_time(clock.now(), 0.0)
        else:
            # we didn't block, so set to predicted flip time
            self.last_flip = event_time(self._next_flip_time, 0.0)

        # update flip times
        self._next_flip_time = self.last_flip['time'] + self.flip_interval
        self._next_draw_time = self.last_flip['time'] + self.flip_interval/2.
        self._did_draw = False

        return self.last_flip

    def get_flip_interval(self):
        # hard code to 60 Hz for now
        kconfig = kivy_overrides._get_config()
        self.flip_interval = 1./kconfig['frame_rate']
        return self.flip_interval

        """    OLD WAY
        diffs = 0.0
        last_time = 0.0
        count = 0.0
        for i in range(nflips):
            # perform the flip and record the flip interval
            cur_time = self.do_flip(block=True)
            if last_time > 0.0 and i >= nignore:
                diffs += cur_time['time'] - last_time['time']
                count += 1
            last_time = cur_time

            # add in sleep of something definitely less than the refresh rate
            clock.usleep(2000)  # 2ms for 500Hz

        # take the mean and return
        self.flip_interval = diffs / count
        return self.flip_interval
        """

    def schedule_video(self, update_cb, flip_time=None, flip_time_cb=None):
        # TODO: Remove None options where possible
        if flip_time is None:
            flip_time = self.last_flip["time"] + self.flip_interval
        new_video = _VideoChange(update_cb, flip_time, flip_time_cb)
        if self.pending_flip_time is not None and \
           flip_time < self.pending_flip_time:
            # can't insert before already prepared pending flip
            # set flip_time to pending_flip_time
            flip_time = self.pending_flip_time
            new_video.flip_time = self.pending_flip_time
        for n, video in enumerate(self.video_queue):
            if video.flip_time > flip_time:
                self.video_queue.insert(n, new_video)
                break
        else:
            self.video_queue.append(new_video)
        return new_video

    def cancel_video(self, video):
        if not video.drawn:
            try:
                self.video_queue.remove(video)
            except ValueError:
                pass

    def screenshot(self, filename=None):
        Window.screenshot(filename)

    def set_background_color(self, color=None):
        if color is None:
            if self.exp._background_color is None:
                return
            color = self.exp._background_color
        Window.clearcolor = normalize_color_spec(color)

    def get_exp_from_file(self, filename=None):
        # process the filename
        if filename is None:
            filename = kivy_overrides.args.experiment

        # set the cwd to that directory
        # cwd = os.getcwd()
        nwd, expfile = os.path.split(filename)
        if nwd != '':
            os.chdir(nwd)

        # execute the file
        #print nwd, expfile
        #import kivy.base
        #EL = kivy.base.EventLoop
        import imp
        m = imp.load_source(expfile[:-3], expfile)
        #m = __import__(expfile[:-3])
        #f, filename, desc = imp.find_module(expfile[:-3],['.'])
        #print f, filename, desc
        #m = imp.load_module(expfile[:-3], f, filename, desc)
        #print m['exp']
        #m = globals()
        # l = locals()
        print(m.exp)
        # print l
        #execfile(expfile, m)

        # kivy.base.EventLoop = EL

        # here's the Python3 equivalent
        # with open(filename) as f:
        #     code = compile(f.read(), filename, 'exec')
        #     exec(code, global_vars, local_vars)

        # return the exp
        #exp = Experiment._last_instance()
        # if exp and isinstance(Experiment, exp):
        #     return exp
        # else:
        #     raise ValueError("The provided file does not
        #     have an Experiment instance.")

        return m.exp
        #return m['exp']

    def run_exp(self, exp=None, filename=None):
        # handle exp
        if exp is None:
            exp = self.get_exp_from_file(filename)

        # stop current exp if necessary
        if self.exp:
            # if self.exp._root_executor._active:
            if self.exp.running:
                # stop it and clean up
                self.exp.finish()
                # self.exp._root_executor.cancel(clock.now())
                # self.exp.clean()

        # link the exp to the app
        exp._app = self

        # link the app to the exp
        self.exp = exp

        # run the exp
        self.exp.start()
        #exp._root_executor.enter(clock.now() + 0.25)

    def start(self):
        # start the app in a try/except to clean up properly
        try:
            # kivy main loop
            self.run()
        except:
            if self.exp:
                # clean up the logs
                self.exp._root_state.end_log(self.exp._csv)
                self.exp.close_state_loggers(self.exp._csv)

                # see if we can traceback
                if self.exp._current_state is not None:
                    self.exp._current_state.print_traceback()

            # raise the error
            raise

    def stop(self, *largs):
        """Make sure you use this to close your app.

        from kivy.base import stopTouchApp
        Config.set('kivy', 'exit_on_escape', '0')
        def end_it():
            stopTouchApp()
        Func(end_it)
        """
        self.root_window.close()
        return super(SmileApp, self). stop(*largs)

if __name__ == '__main__':
    SmileApp().start()
