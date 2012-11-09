#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import State, Wait, Serial
from state import schedule_delayed_interval, schedule_delayed
from utils import rindex
from ref import Ref, val

# get the last instance of the experiment class
from experiment import Experiment

from pyglet import clock
import pyglet

"""
Show, Draw, Flip

The issue is that we only want to Draw once

"""

class VisualState(State):
    def __init__(self, interval=0, duration=1.0, parent=None, reset_clock=False):
        # init the parent class
        super(VisualState, self).__init__(interval=interval, parent=parent, 
                                          duration=duration, reset_clock=reset_clock)

        # get the exp reference
        self.exp = Experiment.last_instance()

        # we haven't shown anything yet
        self.shown = None

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        pass

    def update_callback(self, dt):
        # call the user-defined show
        self.shown = self._update_callback(dt)

        # tell the exp window we need a draw
        self.exp.window.need_draw = True

    def draw_callback(self, dt):
        # call the draw (not forced, so it can skip it)
        self.exp.window.on_draw()

    def _callback(self, dt):
        # call the flip, recording the time
        self.last_flip = self.exp.blocking_flip()
        
    def schedule_update(self, flip_delay):
        # the show will be 1/2 of a flip interval before the flip
        update_delay = flip_delay - self.exp.flip_interval/2
        schedule_delayed_interval(self.update_callback, update_delay, self.interval)

        # the draw will be 1/4 of a flip interval before the flip
        draw_delay = flip_delay - self.exp.flip_interval/4
        schedule_delayed_interval(self.draw_callback, draw_delay, self.interval)

    def _enter(self):
        # the flip will already be scheduled
        # schedule the show
        update_delay = self.state_time - clock._default.time()
        if update_delay < 0:
            update_delay = 0
        self.schedule_update(update_delay)

    def _leave(self):
        # unschedule the various callbacks
        clock.unschedule(self.update_callback)
        clock.unschedule(self.draw_callback)

class Unshow(VisualState):
    def __init__(self, vstate, parent=None, reset_clock=False):
        # init the parent class
        super(Unshow, self).__init__(interval=0, parent=parent, 
                                     duration=0, reset_clock=reset_clock)

        # we haven't shown anything yet
        self.shown = None
        self.vstate = vstate

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        self.shown = self.vstate.shown
        self.shown.delete()
        return self.shown

class Text(VisualState):
    def __init__(self, textstr, x=0, y=0, anchor_x='center', anchor_y='center',
                 font_name=None, font_size=None, color=(255,255,255,255),
                 bold=False, italic=False, halign='center', multiline=False,
                 dpi=None, group=None,
                 parent=None, reset_clock=False):
        super(Text, self).__init__(interval=0, parent=parent, 
                                   duration=0, reset_clock=reset_clock)

        self.textstr = textstr
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.x = x
        self.y = y
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.bold = bold
        self.italic = italic
        self.halign = halign
        self.multiline = multiline
        self.dpi = dpi
        self.group = group
        pass

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        if self.shown:
            # update with the values
            pass
        else:
            # make the new shown and return it
            self.shown = pyglet.text.Label(val(self.textstr),
                                           font_name=val(self.font_name),
                                           font_size=val(self.font_size),
                                           color=val(self.color),
                                           x=val(self.x), y=val(self.y),
                                           anchor_x=val(self.anchor_x), 
                                           anchor_y=val(self.anchor_y),
                                           bold=val(self.bold),
                                           italic=val(self.italic),
                                           halign=val(self.halign),
                                           multiline=val(self.multiline),
                                           dpi=val(self.dpi),
                                           group=self.group,
                                           batch=self.exp.window.batch)
        return self.shown



class Image(VisualState):
    def __init__(self, imgstr, x=0, y=0, flip_x=False, flip_y=False,
                 rotation=0, scale=1.0, opacity=255,
                 parent=None, reset_clock=False):
        super(Image, self).__init__(interval=0, parent=parent, 
                                    duration=0, reset_clock=reset_clock)

        self.imgstr = imgstr
        self.rotation = rotation
        self.scale = scale
        self.opacity = opacity
        self.x = x
        self.y = y
        self.flip_x = flip_x
        self.flip_y = flip_y
        pass

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        if self.shown:
            # update with the values
            pass
        else:
            # make the new shown and return it
            self.img = pyglet.resource.image(val(self.imgstr), 
                                             flip_x=val(self.flip_x),
                                             flip_y=val(self.flip_y))
            self.shown = pyglet.sprite.Sprite(self.img,
                                              x=val(self.x), y=val(self.y),
                                              batch=self.exp.window.batch)
            self.shown.scale = val(self.scale)
            self.shown.rotation = val(self.rotation)
            self.shown.opacity = val(self.opacity)
        return self.shown

        
class Show(Serial):
    """
    Show(Text("jubba"), duration=2.0)
    """
    def __init__(self, vstate, parent=None, duration=1.0, reset_clock=False):
        super(Show, self).__init__(parent=parent, duration=duration, 
                                   reset_clock=reset_clock)

        # remove vstate from parent if it exists
        self.claim_child(vstate)

        # add the wait and unshow states
        Wait(duration, parent=self)
        Unshow(vstate, parent=self)

        # expose the shown
        self.shown = vstate.shown
        


if __name__ == '__main__':

    from experiment import Experiment
    import pyglet
    from state import Parallel

    exp = Experiment()

    Show(Text('Jubba!!!', x=exp.window.width//2, y=exp.window.height//2), 
         duration=1.0, parent=exp)
    Wait(2.0, parent=exp)
    with Parallel(parent=exp) as same:
        Show(Text('Wubba!!!', x=exp.window.width//2, y=exp.window.height//2, 
                  color=(255,0,0,255)), 
             duration=1.0, parent=same)
        Show(Image('face-smile.png', x=exp.window.width//2, y=exp.window.height//2), 
             duration=2.0, parent=same)
    Wait(1.0, parent=exp, stay_active=True)
    exp.run()


         
    
