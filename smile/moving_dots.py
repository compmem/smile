# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from video import WidgetState
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Point
from kivy.properties import NumericProperty, ListProperty

from itertools import chain
import math
import random

__all__ = ['MovingDots']


def random_variance(base, variance):
    return base + variance * (random.random() * 2.0 - 1.0)


class Dot(object):
    def __init__(self, radius=100, scale=1.0,
                 color=[1.0, 1.0, 1.0, 1.0],
                 direction=0, direction_variance=0.0,
                 speed=1.0, speed_variance=0.0,
                 lifespan=.02, lifespan_variance=0.0):

        # process the input vars
        self.radius = radius
        self.scale = scale
        self.color = color
        self.direction = direction
        self.direction_variance = direction_variance
        self.speed = speed
        self.speed_variance = speed_variance
        self.lifespan = lifespan
        self.lifespan_variance = lifespan_variance

        # call reset to initialize the dot loc and dir
        self.reset()

    def update(self, passed_time):
        # update the lifetime
        self.current_time += passed_time

        # reset if past lifetime
        if self.current_time > self.total_time:
            # reset
            self.reset()
            return self.x, self.y

        # update the location
        self.x += self.velocity_x * passed_time
        self.y += self.velocity_y * passed_time

        # reset if outside radius
        if math.sqrt((self.x * self.x) + (self.y * self.y)) > self.radius:
            # must reset
            self.reset()
            return self.x, self.y

        # return x and y
        return self.x, self.y

    def reset(self):
        # determine new location
        '''
        rad = random_variance(0, self.radius)
        loc_angle = random_variance(0, 2*math.pi)
        self.x = (rad * math.cos(loc_angle))
        self.y = (rad * math.sin(loc_angle))
        '''
        t = 2 * math.pi * random.random()
        u = random.random()+random.random()
        if u > 1:
            r = 2-u
        else:
            r = u
        self.x = (self.radius * r * math.cos(t))
        self.y = (self.radius * r * math.sin(t))
        self.start_x = self.x
        self.start_y = self.y

        # process the movement direction
        angle = random_variance(self.direction*math.pi/180,
                                self.direction_variance*math.pi/180)
        speed = random_variance(self.speed, self.speed_variance)
        self.velocity_x = speed * math.cos(angle)
        self.velocity_y = speed * math.sin(angle)

        # set the time
        self.current_time = 0.0
        self.total_time = random_variance(self.lifespan,
                                          self.lifespan_variance)


@WidgetState.wrap
class MovingDots(Widget):
    """
    Moving dot (random dot motion) stimulus.

    Parameters
    ----------
    num_dots : int
        Number of dots active at one time.
    scale : int
        Size in pixels of the dots (really squares)
    radius : int
        Radius of the circle holding the dots.
    lifespan : float
        Mean life of each dot.
    lifespan_variance : float
        Range around the mean lifespan.
    speed : float
        Mean speed of the dots.
    speed_variance : float
        Range around the mean speed.
    coherence : float
        Proportion of dots going in a coherent direction.
        1-coherence will go in random directions.
    direction : float
        Mean direction of the coherent dots in degrees.
    direction_variance : float
        Range around the mean direction.
    color : list
        Color of the dots.
    update_interval : float
        Rate of updating dot locations.

    Examples
    --------

    # now
    MovingDots(coherence=.2, direction=90)

    # the future
    MovingDots(coherence=[.2, .5, .1],
               direction=[0, 120, 240],
               num_dots=200)

    """
    num_dots = NumericProperty(100)
    scale = NumericProperty(4.0)
    radius = NumericProperty(200)
    lifespan = NumericProperty(.75)
    lifespan_variance = NumericProperty(0.5)
    speed = NumericProperty(100.)
    speed_variance = NumericProperty(0)
    coherence = NumericProperty(.5)
    direction = NumericProperty(0)
    direction_variance = NumericProperty(0)
    color = ListProperty([1., 1., 1., 1.])
    update_interval = NumericProperty(1. / 30.)

    def __init__(self, **kwargs):
        super(type(self), self).__init__(**kwargs)

        # set the width and height from radius
        self.width = self.radius*2
        self.height = self.radius*2

        # determine distribution of dots
        # for i in range(0, )
        num_coh = int(round(self.num_dots * self.coherence))
        num_rand = self.num_dots - num_coh

        # generate list of dots
        # first the coherent ones
        self.__dots = [Dot(radius=self.radius, scale=self.scale,
                           color=self.color,
                           direction=self.direction,
                           direction_variance=self.direction_variance,
                           speed=self.speed,
                           speed_variance=self.speed_variance,
                           lifespan=self.lifespan,
                           lifespan_variance=self.lifespan_variance)
                       for i in xrange(num_coh)]

        # then append the non-coh
        self.__dots.extend([Dot(radius=self.radius, scale=self.scale,
                                color=self.color,
                                direction=0.0,
                                direction_variance=360,
                                speed=self.speed,
                                speed_variance=self.speed_variance,
                                lifespan=self.lifespan,
                                lifespan_variance=self.lifespan_variance)
                            for i in xrange(num_rand)])

        # shuffle that list
        random.shuffle(self.__dots)

        Clock.schedule_once(self._update, self.update_interval)

    def _update(self, dt):
        # advance time and locs for all dots
        bases = (self.x + self.scale, self.y+self.scale)
        locs = [bases[i % 2]+p+self.radius
                for i, p in enumerate(chain.from_iterable([d.update(dt)
                                                           for d in
                                                           self.__dots]))]

        # draw the dots
        self.canvas.clear()
        with self.canvas:
            # set the dot color
            Color(*self.color)

            # draw all the dots at their current locations
            Point(points=locs, pointsize=self.scale)

        # schedule next update
        Clock.schedule_once(self._update, self.update_interval)


if __name__ == '__main__':

    from experiment import Experiment
    from state import UntilDone, Wait, Loop
    from keyboard import KeyPress

    exp = Experiment(background_color=("purple", .3))

    Wait(.5)

    with Loop([0, 120, 240, 360]) as trial:
        g = MovingDots(direction=trial.current)
        with UntilDone():
            KeyPress()
        Wait(.25)

    exp.run(trace=False)
