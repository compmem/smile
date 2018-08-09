# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from .video import WidgetState
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
                 lifespan=.02, lifespan_variance=0.0, **kwargs):

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

class BlackHole(object):
    def __init__(self, **kwargs):
        super(BlackHole, self).__init__()

class _MovingDotsWidget(Widget, BlackHole):
    motion_props = ListProperty([{}])
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
        self.width = self.radius * 2
        self.height = self.radius * 2

        # grab default motion params
        default_params = {"radius": self.radius,
                          "scale": self.scale,
                          "color": self.color,
                          "direction": self.direction,
                          "direction_variance": self.direction_variance,
                          "speed": self.speed,
                          "speed_variance": self.speed_variance,
                          "lifespan": self.lifespan,
                          "lifespan_variance": self.lifespan_variance,
                          "coherence": self.coherence}

        # determine distribution of dots
        tot_coh = 0
        self.__dots = []

        # first create the coherent dots
        for mprop in self.motion_props:
            current_params = default_params.copy()
            current_params.update(mprop)
            num_coh = int(self.num_dots * current_params['coherence'])
            tot_coh += num_coh
            self.__dots.extend([Dot(**current_params)
                                for i in range(num_coh)])
        # calc the number random coh
        num_rand = self.num_dots - tot_coh
        if num_rand < 0:
            raise ValueError('Total coherence must be less than 1.0.')

        # now append the non-coh
        if num_rand > 0:
            # there are dots left to place based on the defaults
            current_params = default_params.copy()
            current_params['direction'] = 0.0
            current_params['direction_variance'] = 360
            self.__dots.extend([Dot(**current_params)
                                for i in range(num_rand)])

        self.bind(motion_props=self.callback_motion_props)

        # shuffle that list
        random.shuffle(self.__dots)

        # prepare to keep track of updates
        self._dt_avg = 0.0
        self._avg_n = 0.0

        # not currently running
        self._active = False

    def callback_motion_props(self, obj, value):
        # Grab the current default values for all of
        # our parameters
        default_params = {"radius": self.radius,
                           "scale": self.scale,
                           "color": self.color,
                           "direction": self.direction,
                           "direction_variance": self.direction_variance,
                           "speed": self.speed,
                           "speed_variance": self.speed_variance,
                           "lifespan": self.lifespan,
                           "lifespan_variance": self.lifespan_variance,
                           "coherence": self.coherence}

        tot_coh = 0
        # loop through the updated values for motion props
        for mprop in self.motion_props:
            # Copy the default parameters and only update the given parameters
            current_params = default_params.copy()
            current_params.update(mprop)

            # Calculate how many dots need to get updated for this coherence
            num_coh = int(self.num_dots * mprop['coherence'])
            # Loop through that many dots and update their motion properties
            for i in range(tot_coh, tot_coh + num_coh):                
                self.__dots[i].direction = current_params['direction']
                self.__dots[i].direction_variance = current_params['direction_variance']
                self.__dots[i].speed = current_params['speed']
                self.__dots[i].speed_variance = current_params['speed_variance']
                self.__dots[i].lifespan = current_params['lifespan']
                self.__dots[i].lifespan_variance = current_params['lifespan_variance']

            tot_coh += num_coh
        # For all remaining dots, give them a 0 direction and 360 direction
        # variance. Keep all remaining props as the default params
        if tot_coh < self.num_dots:
            for i in range(tot_coh, self.num_dots):
                
                self.__dots[i].direction = 0
                self.__dots[i].direction_variance = 360
                self.__dots[i].speed = default_params['speed']
                self.__dots[i].speed_variance = default_params['speed_variance']
                self.__dots[i].lifespan = default_params['lifespan']
                self.__dots[i].lifespan_variance = default_params['lifespan_variance']

    def start(self):
        Clock.schedule_once(self._update, self.update_interval)
        self._active = True

    def stop(self):
        self._active = False

    def _update(self, dt):
        # update the dt_avg
        self._avg_n += 1.0
        self._dt_avg += (dt - self._dt_avg) / self._avg_n

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
        if self._active:
            Clock.schedule_once(self._update, self.update_interval)

    @property
    def refresh_rate(self):
        return 1.0 / self._dt_avg

class MovingDots(WidgetState.wrap(_MovingDotsWidget)):
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
    motion_props : list of dicts
        List of properties governing dot motion.
    """
    def show(self):
        # custom show so that the widget doesn't run when not onscreen
        self._widget.start()
        super(MovingDots, self).show()

    def unshow(self):
        # custom unshow so that the widget doesn't run when not onscreen
        super(MovingDots, self).unshow()
        self._widget.stop()


if __name__ == '__main__':

    from .experiment import Experiment
    from .state import UntilDone, Meanwhile, Wait, Loop, Debug
    from .keyboard import KeyPress

    # A testing set to show all the different things you can change when
    # setting motion_props during run-time.
    testing_set = [[{"coherence": 0.1, "direction": 0,
                     "direction_variance": 0, "speed":400},
                    {"coherence": 0.5, "direction": 180,
                     "direction_variance": 0, "speed":50},],
                   [{"coherence": 0.5, "direction": 0,
                     "direction_variance": 0, "speed":50,
                     "lifespan":.6, "lifespan_variance":.5},
                    {"coherence": 0.1, "direction": 180,
                     "direction_variance": 10, "speed":400,
                     "speed_variance":200},]
                  ]
    exp = Experiment(background_color=("purple", .3), debug=True)

    Wait(.5)

    g = MovingDots(radius=300,
                   scale=10,
                   num_dots=4,
                   motion_props=[{"coherence": 0.25, "direction": 0,
                                  "direction_variance": 0},
                                 {"coherence": 0.25, "direction": 90,
                                  "direction_variance": 0},
                                 {"coherence": 0.25, "direction": 180,
                                  "direction_variance": 0},
                                 {"coherence": 0.25, "direction": 270,
                                  "direction_variance": 0}])
    with UntilDone():
        KeyPress()
        with Meanwhile():
            g.slide(color='red', duration=4.0)
    Wait(.25)

    with Loop(4):
        MovingDots()
        with UntilDone():
            KeyPress()

    md = MovingDots(radius=300, scale=3, num_dots=200,
                    motion_props=[{"coherence": 0.25, "direction": 0,
                                   "direction_variance": 0},
                                  {"coherence": 0.25, "direction": 180,
                                   "direction_variance": 0},])
    with UntilDone():
        with Loop(testing_set) as ts:
            Wait(3.)
            md.motion_props = ts.current
        Wait(5.)

    Debug(rate=g.widget.refresh_rate)
    exp.run(trace=False)
