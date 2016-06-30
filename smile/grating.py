#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from video import WidgetState
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.graphics import Rectangle, BindTexture, Callback
from kivy.graphics.texture import Texture
from kivy.graphics.opengl import glBlendFunc, GL_SRC_ALPHA
from kivy.graphics.opengl import GL_ONE_MINUS_SRC_ALPHA
from kivy.graphics.opengl import GL_ONE_MINUS_DST_ALPHA
from array import array
import math
from itertools import chain
# cache so we don't regenerate masks
_mask_cache = {}

@WidgetState.wrap
class Grating(Widget):
    """Display a Grating
    *Only renders square sized grating textures*

    Parameters
    ----------
    color_one : list
        rgba the Grating will oscillate between
    color_two : list
        rgba the Grating will oscillate between
    envelope : string
        type of Grating to be generated
    frequency : float
        frequency of sign wave of Grating
    phase : float
        the phase shift of the sin wave
    std_dev : integer
        the standard deviation of sin wave

    """

    envelope = StringProperty('g')
    frequency = NumericProperty(20)
    std_dev = NumericProperty(20)
    phase = NumericProperty(0.0)
    color_one = ListProperty([1., 1., 1.])
    color_two = ListProperty([0., 0., 0.])

    def __init__(self, **kwargs):
        super(type(self), self).__init__(**kwargs)

        self._texture = None
        self._mask_texture = None

        self.bind(envelope=self._update_texture,
                  std_dev=self._update_texture,
                  phase=self._update_texture,
                  color_one=self._update_texture,
                  color_two=self._update_texture,
                  frequency=self._update_texture,
                  pos=self._update,
                  size=self._update_texture)
        self._update_texture()

    def _calc_mask(self, rx, ry):
        dx = rx - (self.width/2)   # horizontal center of Grating
        dy = ry - (self.height/2)  # vertical center of Grating

        t = math.atan2(dy, dx)
        radius = math.sqrt(dx ** 2 + dy ** 2)
        ux = radius * math.cos(t)
        uy = radius * math.sin(t)
        #Gaussian Gabor stimuli calculations
        if self.envelope[0] == 'g' or self.envelope[0] == 'G':
            transparency = math.exp(-0.5 * (ux / (self.std_dev*3)) ** 2 - 0.5 *
                         (uy / (self.std_dev*3)) ** 2)
        #Linear Gabor stimuli calculations
        elif self.envelope[0] == 'l' or self.envelope[0] == 'L':
            transparency = max(0, (0.5 * self.width - radius) / (0.5 * self.width))
        #Circular Gabor stimuli calculations
        elif self.envelope[0] == 'c' or self.envelope[0] == 'C':
            if (radius > 0.5 * self.width):
                transparency = 0.0
            else:
                transparency = 1.0
        else:
            transparency = 1.0
        transparency = 1.0 - transparency
        #Return
        return 0, 0, 0, transparency

    def _calc_color(self, x):
        #Creation of the sin wave for the grating texture
        amp = 0.5 + 0.5 * math.sin((x*math.pi/180) * self.frequency + self.phase)
        #RGB color return
        return [(self.color_one[0] * amp + self.color_two[0] * (1.0 - amp)),
                (self.color_one[1] * amp + self.color_two[1] * (1.0 - amp)),
                (self.color_one[2] * amp + self.color_two[2] * (1.0 - amp))]

    #Updates textures by calling update functions
    def _update_texture(self, *pargs):
        self._update_grating()
        if self._mask_texture is None or \
           self.size != self._prev_size or \
           self.std_dev != self._prev_std_dev:
            self._update_mask()
            self._prev_size = self.size
            self._prev_std_dev = self.std_dev
        self._update()

    #Updates the drawling of the textures on screen
    def _update(self, *pargs):
        # clear (or else we get gratings all over)
        self.canvas.clear()

        # set up the blending
        with self.canvas.before:
            Callback(self._set_blend_func)

        # Draw the two textures in rectangles
        with self.canvas:
            # draw the mask
            mask = Rectangle(size=self.size, pos=self.pos,
                             texture=self._mask_texture)
            #repeats 4 times to fill the created texture rectangle
            mask.tex_coords = 0, 0, 2, 0, 2, 2, 0, 2

            # draw the grating
            grating = Rectangle(size=self.size, pos=self.pos,
                                texture=self._texture)
            #repeats the grating to fill the texture rectangle
            grating.tex_coords = (0, 0, self.width/self._period,
                                  0, self.width/self._period,
                                  self.height, 0, self.height)

        # clean up the blending
        with self.canvas.after:
            Callback(self._reset_blend_func)

    #Update grating variables
    def _update_grating(self, *args):
        # calculate the num needed for period
        self._period = int(round(360./self.frequency))

        # make new texture
        self._texture = Texture.create(size=(self._period, 1),
                                       colorfmt='rgb',
                                       bufferfmt='float')

        # fill the buffer for the texture
        grating_buf = list(chain.from_iterable([self._calc_color(x)
                                                for x in range(self._period)]))
        # make an array from the buffer
        grating_arr = array('f', grating_buf)

        # blit the array to the texture
        self._texture.blit_buffer(grating_arr, colorfmt='rgb',
                                  bufferfmt='float')

        # set it to repeat
        self._texture.wrap = 'repeat'
        BindTexture(texture=self._texture, index=0)

    #Update Mask variables
    def _update_mask(self, *args):
        #creation of texture, half the width and height, will be reflected to
        #completely cover the grating texture
        self._mask_texture = Texture.create(size=(self.width/2, self.height/2),
                                            colorfmt='rgba')

        # generate a unique mask id for cache lookup
        mask_id = 'e%s_w%d_h%d'%(self.envelope, self.width, self.height)
        global _mask_cache

        try:
            # see if we've already created this mask
            mask_arr = _mask_cache[mask_id]
        except KeyError:
            # set mask (this is the slow part)
            mask_buf = list(chain.from_iterable([self._calc_mask(rx, ry)
                                                 for rx in range(self.width/2)
                                                 for ry in range(self.height/2)]))
            # turn into an array
            mask_arr = array('f', mask_buf)

            # add it to the cache
            _mask_cache[mask_id] = mask_arr

        # blit it
        self._mask_texture.blit_buffer(mask_arr, colorfmt='rgba',
                                       bufferfmt='float')
        #mask is mirrored and repeated
        self._mask_texture.wrap = 'mirrored_repeat'
        #mask is set to foremost texture
        self._mask_texture.mag_filter = 'nearest'
        BindTexture(texture=self._mask_texture, index=1)

    #Controller for the Gabor blending to the background color
    #glBlendFunc(starting RGBA values, desired RGBA values)
    def _set_blend_func(self, instruction):
        glBlendFunc(GL_ONE_MINUS_DST_ALPHA, GL_SRC_ALPHA)

    #Reset of the Gabor blending properties for creation of new stimuli
    #glBlendFunc(starting RGBA values, desired RGBA values)
    def _reset_blend_func(self, instruction):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


if __name__ == '__main__':

    from experiment import Experiment
    from state import UntilDone, Wait, Parallel, Serial
    from keyboard import KeyPress
    from video import Label

    exp = Experiment(background_color="#4F33FF")

    g = Grating(width=500, height=500, envelope='Circular', frequency=50,
                std_dev=50, phase=9.0, color_one='orange', color_two='blue')
    with UntilDone():
        KeyPress()
        g.update(bottom=exp.screen.center)
        KeyPress()

    g = Grating(width=1000, height=1000, envelope='linear', frequency=20,
                std_dev=10, phase=3.0, color_one='red', color_two='yellow')
    with UntilDone():
        KeyPress()
        g.update(bottom=exp.screen.center)
        KeyPress()

    g = Grating(width=200, height=200, envelope='Gaussian', frequency=75,
                std_dev=7, phase=11.0, color_one='blue', color_two='red')
    with UntilDone():
        KeyPress()
        g.update(bottom=exp.screen.center)
        KeyPress()

    with Parallel():
        g = Grating(width=256, height=256, frequency=20,
                  std_dev=10,
                  color_one='green', color_two='orange')
        lbl = Label(text='Grating!', bottom=g.top)
    with UntilDone():
        # kp = KeyPress()
        with Parallel():
            g.slide(phase=-8*math.pi, #frequency=10.,
                    #bottom=exp.screen.bottom,
                    duration=6.)
            g.slide(rotate=90, duration=2.0)
            with Serial():
                Wait(2.0)
                lbl.slide(top=g.bottom, duration=4.)

    with Parallel():
        g = Grating(width=256, height=256, frequency=10,
                  std_dev=10,
                  color_one='blue', color_two='red')
        lbl = Label(text='Grating!', bottom=g.top)
    with UntilDone():
        kp = KeyPress()
        with Parallel():
            g.slide(phase=-8*math.pi, frequency=10.,
                    bottom=exp.screen.bottom,
                    duration=6.)
            g.slide(rotate=90, duration=2.0)
            with Serial():
                Wait(2.0)
                lbl.slide(top=g.bottom, duration=4.)


    exp.run(trace=False)