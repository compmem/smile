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
from ref import Ref, val

# get the last instance of the experiment class
from experiment import Experiment, now

from pyglet import clock
import pyglet


class VisualState(State):
    """
    Parent state that handles drawing and showing of a visual
    stimulus.

    The key is to register that we want a flip, but only flip once if
    multiple stimuli are to be shown at the same time.
    """
    def __init__(self, interval=0, duration=1.0, parent=None, 
                 reset_clock=False, save_log=True):
        # init the parent class
        super(VisualState, self).__init__(interval=interval, parent=parent, 
                                          duration=duration, 
                                          reset_clock=reset_clock,
                                          save_log=save_log)

        # we haven't shown anything yet
        self.shown = None
        self.last_update = 0
        self.last_flip = 0
        self.last_draw = 0
        self.first_update = 0
        self.first_flip = 0
        self.first_draw = 0

        # set the log attrs
        self.log_attrs.extend(['last_draw', 'last_update', 'last_flip'])
                               
    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        pass

    def update_callback(self, dt):
        # call the user-defined show
        self.shown = self._update_callback(dt)
        self.last_update = now()
        if self.first_update == 0:
            self.first_update = self.last_update

        # tell the exp window we need a draw
        self.exp.window.need_draw = True

    def draw_callback(self, dt):
        # call the draw (not forced, so it can skip it)
        self.exp.window.on_draw()
        self.last_draw = now()
        if self.first_draw == 0:
            self.first_draw = self.last_draw

    def _callback(self, dt):
        # call the flip, recording the time
        self.last_flip = self.exp.blocking_flip()
        if self.first_flip == 0:
            self.first_flip = self.last_flip
        
    def schedule_update(self, flip_delay):
        # the show will be 3/4 of a flip interval before the flip
        update_delay = flip_delay - self.exp.flip_interval*3/4.
        if update_delay <= 0:
            # do it now
            self.update_callback(0)
            
            # if interval, must still schedule it
            if self.interval > 0:
                schedule_delayed_interval(self.update_callback, 
                                          self.interval - self.exp.flip_interval*3/4., 
                                          self.interval)
        else:
            schedule_delayed_interval(self.update_callback, 
                                      update_delay, self.interval)

        # the window draw will be 1/2 of a flip interval before the flip
        draw_delay = flip_delay - self.exp.flip_interval/2.
        if draw_delay <= 0:
            # do it now
            self.draw_callback(0)

            # if interval, must still schedule it
            if self.interval > 0:
                schedule_delayed_interval(self.draw_callback, 
                                          self.interval - self.exp.flip_interval/2., 
                                          self.interval)
        else:
            schedule_delayed_interval(self.draw_callback, 
                                      draw_delay, self.interval)

    def _enter(self):
        # reset times
        self.last_update = 0
        self.last_flip = 0
        self.last_draw = 0
        self.first_update = 0
        self.first_flip = 0
        self.first_draw = 0

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


class Update(VisualState):
    """
    Visual state to update a shown item.
    """
    def __init__(self, vstate, attr, value,
                 parent=None, reset_clock=False, save_log=True):
        # init the parent class
        super(Update, self).__init__(interval=0, parent=parent, 
                                     duration=0, reset_clock=reset_clock,
                                     save_log=save_log)

        # we haven't shown anything yet
        self.shown = None
        self.vstate = vstate
        self.attr = attr
        self.value = value

        # update more log attrs
        self.log_attrs.extend(['attr', 'value'])

    def _update_callback(self, dt):
        self.shown = val(self.vstate).shown
        setattr(self.shown,
                val(self.attr),
                val(self.value))


class Unshow(VisualState):
    """
    Visual state to unshow a shown item.
    """
    def __init__(self, vstate, parent=None, reset_clock=False, save_log=True):
        # init the parent class
        super(Unshow, self).__init__(interval=0, parent=parent, 
                                     duration=0, reset_clock=reset_clock,
                                     save_log=save_log)

        # we haven't shown anything yet
        self.shown = None
        self.vstate = vstate

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        self.vstate = val(self.vstate)
        self.shown = self.vstate.shown
        if self.shown:
            self.shown.delete()
            self.shown = None
            self.vstate.shown = None
        return self.shown


class Text(VisualState):
    """
    Visual state to present text.
    """
    def __init__(self, textstr, x=0, y=0, anchor_x='center', anchor_y='center',
                 font_name=None, font_size=18, color=(255,255,255,255),
                 bold=False, italic=False, halign='center', 
                 width=None, height=None, multiline=False,
                 dpi=None, group=None,
                 parent=None, reset_clock=False, save_log=True):
        super(Text, self).__init__(interval=0, parent=parent, 
                                   duration=0, reset_clock=reset_clock,
                                   save_log=save_log)

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
        self.width = width
        self.height = height
        self.multiline = multiline
        self.dpi = dpi
        self.group = group

        self.log_attrs.extend(['textstr', 'font_name', 'font_size', 'color',
                               'x', 'y', 'anchor_x', 'anchor_y', 'bold',
                               'italic', 'halign', 'width', 'height', 'multiline'])

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
                                           width=val(self.width),
                                           height=val(self.height),
                                           multiline=val(self.multiline),
                                           dpi=val(self.dpi),
                                           group=self.group,
                                           batch=self.exp.window.batch)
        return self.shown


class Image(VisualState):
    """
    Visual state to present an image.
    """
    def __init__(self, imgstr, x=0, y=0, flip_x=False, flip_y=False,
                 rotation=0, scale=1.0, opacity=255,
                 parent=None, reset_clock=False, save_log=True):
        super(Image, self).__init__(interval=0, parent=parent, 
                                    duration=0, reset_clock=reset_clock,
                                    save_log=save_log)

        self.imgstr = imgstr
        self.rotation = rotation
        self.scale = scale
        self.opacity = opacity
        self.x = x
        self.y = y
        self.flip_x = flip_x
        self.flip_y = flip_y

        # append log attrs
        self.log_attrs.extend(['imgstr', 'rotation', 'scale', 'opacity',
                               'x', 'y', 'flip_x', 'flip_y'])
        
        pass

    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        if not self.shown is None:
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


class Movie(VisualState):
    """
    Visual state to present an movie.
    """
    def __init__(self, movstr, x=0, y=0,
                 rotation=0, scale=1.0, opacity=255, framerate=1/30.,
                 parent=None, reset_clock=False, save_log=True):
        super(Movie, self).__init__(interval=framerate, parent=parent, 
                                    duration=-1, reset_clock=reset_clock,
                                    save_log=save_log)

        self.movstr = movstr
        self.rotation = rotation
        self.scale = scale
        self.opacity = opacity
        self.x = x
        self.y = y

        self._player = pyglet.media.Player()
        self._player.eos_action = self._player.EOS_PAUSE

        # append log attrs
        self.log_attrs.extend(['movstr', 'rotation', 'scale', 'opacity',
                               'x', 'y'])
        
        pass

    def _enter(self):
        # load the media
        self._source = pyglet.media.load(val(self.movstr))

        # pop off any current sources
        while self._player.source:
            self._player.next()

        # queue source
        self._player.queue(self._source)

        # process enter from parent (VisualState)
        super(Movie, self)._enter()


    def _update_callback(self, dt):
        # children must implement drawing the showable to make it shown
        if not self.shown is None:
            # update with the values
            if not self._player.playing:
                if self.shown:
                    self.shown.delete()
                    self.shown = None
                self.leave()
                return None
                
            if self._player.source: 
                img = self._player.get_texture()
            else:
                img = None
            if img is None:
                self._player.pause()
                if self.shown:
                    self.shown.delete()
                    self.shown = None
                self.leave()
                return None
            self.shown.image = img
        else:
            # if playing, then stopped from outside
            if self._player.playing:
                # we need to leave
                self._player.pause()
                self.leave()
                return None
            # make the new shown and return it
            # star the player
            self._player.play()

            # get the image
            img = self._player.get_texture()
            
            if img is None:
                self._player.pause()
                if self.shown:
                    self.shown.delete()
                    self.shown = None
                self.leave()
                return None
            self.shown = pyglet.sprite.Sprite(img,
                                              x=val(self.x), y=val(self.y),
                                              batch=self.exp.window.batch)
            self.shown.scale = val(self.scale)
            self.shown.rotation = val(self.rotation)
            self.shown.opacity = val(self.opacity)

        return self.shown

    def _leave(self):
        # process leave from parent (VisualState)
        super(Movie, self)._leave()

        # stop playing if not already
        self._player.pause()

        # pop off any current sources
        while self._player.source:
            self._player.next()

        
class Show(Serial):
    """
    Show a visual state for a specified duration before unshowing it.
    
    Show(Text("jubba"), duration=2.0)
    """
    def __init__(self, vstate, parent=None, duration=1.0, 
                 reset_clock=False, save_log=True):
        super(Show, self).__init__(parent=parent, duration=duration, 
                                   reset_clock=reset_clock,
                                   save_log=save_log)

        # remove vstate from parent if it exists
        self.claim_child(vstate)

        # add the wait and unshow states
        self._show_state = vstate
        self._wait_state = Wait(duration, parent=self)
        self._unshow_state = Unshow(vstate, parent=self)

        # expose the shown
        self.shown = vstate.shown

        # save the show and hide times
        self.show_time = Ref(self._show_state,'first_flip')
        self.unshow_time = Ref(self._unshow_state,'first_flip')

        # append times to log
        self.log_attrs.extend(['show_time','unshow_time'])

        
if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    import pyglet
    from state import Parallel, Loop, Func

    exp = Experiment()

    Wait(.5)
    
    # Show(Text('Jubba!!!', x=exp.window.width//2, y=exp.window.height//2), 
    #      duration=1.0)
    # Wait(1.0)
    # with Parallel():
    #     Show(Text('Wubba!!!', x=exp.window.width//2, y=exp.window.height//2, 
    #               color=(255,0,0,255)), 
    #          duration=1.0)
    #     Show(Image('face-smile.png', x=exp.window.width//2, y=exp.window.height//2), 
    #          duration=2.0)

    # Wait(1.0)


    def print_dt(state, *txt):
        for t in txt:
            print t
        print now()-state.state_time, state.dt
        print
    
    block = [{'text':['a','b','c']},
             {'text':['d','e','f']},
             {'text':['g','h','i']}]
    with Loop(block) as trial:
        Set('stim_times',[])
        with Loop(trial.current['text']) as item:
            ss = Show(Text(item.current.value, 
                      x=exp.window.width//2, 
                      y=exp.window.height//2, 
                      color=(255,0,0,255)),
                      duration=1.0)
            #Wait(1.0)
            #Unshow(ss)
            Wait(.5)
            #Set('stim_times',Get('stim_times')+[ss['last_flip']])
            #Set('stim_times',Get('stim_times')+[ss['show_time']])
            Set('stim_times',Get('stim_times').append(ss.show_time))
            #Set('stim_times',
            #    Get('stim_times')+Ref(gfunc=lambda : list(ss.show_time)))

            Func(print_dt, args=[ss.show_time,Get('stim_times')])
                        
    Wait(1.0, stay_active=True)
    exp.run()


         
    
