# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .video import WidgetState
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.graphics import Rectangle, BindTexture, Callback
from kivy.graphics.texture import Texture
from kivy.graphics.opengl import glBlendFunc, GL_SRC_ALPHA
from kivy.graphics.opengl import GL_ONE_MINUS_SRC_ALPHA
from kivy.graphics.opengl import GL_ONE_MINUS_DST_ALPHA
import math
from itertools import chain

#@FIX: import six
import six


# cache so we don't regenerate masks
_mask_cache = {}


@WidgetState.wrap
class Grating(Widget):
    """Creates a masked grating.

    The grating can be masked by either a Gaussian, linear, or
    circular mask. Due to the limitations of Kivy, this widget can
    only create square textures.

    Parameters
    ----------
    color_one : list
        first rgb color(each value between zero to one) which the grating will
        oscillate between
    color_two : list
        first rgb color(each value between zero to one) which the grating will
        oscillate between
    envelope : string
        type of Grating to be generated
        - Gaussian: creates a circular, Gaussian algorithm-based mask which
                    becomes more transparent the more distant from the center
        - Linear: creates a circular, linear algorithm-based mask which becomes
                  more transparent the more distant from the center
        - Circular: creates a circular mask which has no blending to the
                    background
    frequency : float
        frequency of sine wave of Grating
    phase : float
        the phase shift of the sin wave
    std_dev : integer
        the standard deviation of the Gaussian mask controlling the size of the
        mask. Larger values create a larger grating on screen due to greater
        transparency and smaller values create smaller grating on screen due to
        less transparency.

    """

    envelope = StringProperty('g')
    frequency = NumericProperty(20)
    std_dev = NumericProperty(None)
    phase = NumericProperty(0.0)
    color_one = ListProperty([1., 1., 1., 1.])
    color_two = ListProperty([0., 0., 0., 0.])
    contrast = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super(type(self), self).__init__(**kwargs)

        if self.std_dev is None:
            self.std_dev = (self.width / 2) * 0.1

        self._texture = None
        self._mask_texture = None
        self._period = None

        self.bind(envelope=self._update_texture,
                  std_dev=self._update_texture,
                  phase=self._update_texture,
                  color_one=self._update_texture,
                  color_two=self._update_texture,
                  frequency=self._update_texture,
                  pos=self._update,
                  size=self._update_texture,
                  contrast=self._update_texture)
        self._update_texture()

    def _calc_gaussian_mask(self, rx, ry):
        '''Performs the calculation for the mask either Gaussian, linear, or circular.
        The function creates the bottom left quadrant of the mask, then mirrors
        and repeats the texture 3 times in the top left, top right, and bottom
        left quadrants'''
        dx = rx - (self.width / 2.)   # horizontal center of Grating
        dy = ry - (self.height / 2.)  # vertical center of Grating

        # Gaussian Gabor stimuli calculations
        transparency = math.exp(-0.5 *
                                (dy / (self.std_dev * math.pi)) ** 2 -
                                0.5 *
                                (dx / (self.std_dev * math.pi)) ** 2)

        return 0, 0, 0, int(round((1 - transparency) * 255))  # 0 is no alpha

    def _calc_linear_mask(self, rx, ry):
        dx = rx - (self.width / 2.)   # horizontal center of Grating
        dy = ry - (self.height / 2.)  # vertical center of Grating
        radius = math.sqrt(dx ** 2 + dy ** 2)

        transparency =\
            max(0, (0.5 * self.width - radius) / (0.5 * self.width))

        return 0, 0, 0, int(round((1 - transparency)*255))  # 0 is no alpha

    def _calc_circular_mask(self, rx, ry):
        dx = rx - (self.width / 2.)   # horizontal center of Grating
        dy = ry - (self.height / 2.)  # vertical center of Grating
        radius = math.sqrt(dx ** 2 + dy ** 2)
        if (radius > 0.5 * self.width):
            transparency = 0.0
        else:
            transparency = 1.0
        return 0, 0, 0, int(round((1 - transparency)*255))  # 0 is no alpha

    def _calc_undefined_mask(self, rx, ry):
        transparency = 1.0
        # Return
        return 0, 0, 0, int(round((1 - transparency)*255))  # 0 is no alpha

    def _calc_color(self, x):
        '''Performs the calculation for the grating behind the mask

        This works by creating one period of a sin wave, then using
        tex_coords, a repeat function not residing in this function to
        fill the rectangle with the grating

        '''

        # Creation of the sin wave for the grating texture
        amp = ((self.contrast *
                (0.5 + 0.5 * math.sin((x * math.pi / 180) *
                                      self.frequency + self.phase))) +
               (1.0 - self.contrast) / 2)

        # RGB color return
        return (int((self.color_one[0] * amp + self.color_two[0] *
                     (1.0 - amp))*255),
                int((self.color_one[1] * amp + self.color_two[1] *
                     (1.0 - amp))*255),
                int((self.color_one[2] * amp + self.color_two[2] *
                     (1.0 - amp))*255))

    def _update_texture(self, *pargs):
        '''Updates textures by calling update functions'''

        self._update_grating()
        if self._mask_texture is None or \
           self.size != self._prev_size or \
           self.std_dev != self._prev_std_dev:
            self._update_mask()
            self._prev_size = self.size
            self._prev_std_dev = self.std_dev
        self._update()

    def _update(self, *pargs):
        '''Updates the drawling of the textures on screen

        The function mirror repeats the mask 3 times in the top left,
        top right and bottom left quadrant to increase
        efficiency. Also it repeats the sin wave, created in the
        _calc_color function to fill the rectangle with the sin wave
        based grating.

        '''
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

            # repeats 4 times to fill the created texture rectangle
            mask.tex_coords = 0, 0, 2, 0, 2, 2, 0, 2

            # draw the grating
            grating = Rectangle(size=self.size, pos=self.pos,
                                texture=self._texture)

            # repeats the grating to fill the texture rectangle
            grating.tex_coords = (0, 0, self.width / self._period,
                                  0, self.width / self._period,
                                  self.height, 0, self.height)

        # clean up the blending
        with self.canvas.after:
            Callback(self._reset_blend_func)

    def _update_grating(self, *args):
        '''Update grating variables

        The function calls the _calc_color function to create the
        grating texture which is layered behind the mask.

        '''
        # calculate the num needed for period
        self._period = int(round(360. / self.frequency))

        # make new texture
        self._texture = Texture.create(size=(self._period, 1),
                                       colorfmt='rgb',
                                       bufferfmt='ubyte')

        # fill the buffer for the texture
        grating_buf = list(chain.from_iterable([self._calc_color(x)
                                                for x in range(self._period)]))
        # make an array from the buffer
        #@FIX: changed
        #grating_arr = b''.join(list(map(chr, grating_buf)))
        grating_arr = b''.join(list(map(lambda x: six.int2byte(x), grating_buf)))

        # blit the array to the texture
        self._texture.blit_buffer(grating_arr, colorfmt='rgb',
                                  bufferfmt='ubyte')

        # set it to repeat
        self._texture.wrap = 'repeat'
        BindTexture(texture=self._texture, index=0)

    def _update_mask(self, *args):
        '''Update Mask variables

        The function calls the mask creating function. Also, it stores
        masks in a cache, for later use to increase function
        efficiency.

        '''

        # creation of texture, half the width and height, will be reflected to
        # completely cover the grating texture
        self._mask_texture = Texture.create(size=(self.width // 2,
                                                  self.height // 2),
                                            colorfmt='rgba',
                                            bufferfmt='ubyte')

        # generate a unique mask id for cache lookup
        mask_id = 'e%s_w%d_h%d_sd%f' % (self.envelope[0].lower(),
                                        self.width, self.height,
                                        self.std_dev)
        global _mask_cache

        try:
            # see if we've already created this mask
            mask_arr = _mask_cache[mask_id]
        except KeyError:
            # set mask (this is the slow part)
            if self.envelope[0].lower() == 'g':
                mask_buf =\
                    list(chain.from_iterable([
                        self._calc_gaussian_mask(rx, ry)
                        #@FIX: changed / to //
                        for rx in range(self.width // 2)
                        for ry in range(self.height // 2)]))
            elif self.envelope[0].lower() == 'l':
                mask_buf =\
                    list(chain.from_iterable([
                        self._calc_linear_mask(rx, ry)
                        for rx in range(self.width // 2)
                        for ry in range(self.height // 2)]))
            elif self.envelope[0].lower() == 'c':
                mask_buf =\
                    list(chain.from_iterable([
                        self._calc_circular_mask(rx, ry)
                        for rx in range(self.width // 2)
                        for ry in range(self.height // 2)]))
            else:
                mask_buf =\
                    list(chain.from_iterable([
                        self._calc_undefined_mask(rx, ry)
                        for rx in range(self.width // 2)
                        for ry in range(self.height // 2)]))
            # turn into an array
            #@FIX: updated byte
            #mask_arr = b''.join(map(chr, mask_buf))
            mask_arr = b''.join(list(map(lambda x: six.int2byte(x), mask_buf)))
            # print mask_arr
            # add it to the cache
            _mask_cache[mask_id] = mask_arr

        # blit it
        self._mask_texture.blit_buffer(mask_arr, colorfmt='rgba',
                                       bufferfmt='ubyte')

        # mask is mirrored and repeated
        self._mask_texture.wrap = 'mirrored_repeat'

        # mask is set to foremost texture
        self._mask_texture.mag_filter = 'nearest'
        BindTexture(texture=self._mask_texture, index=1)

    def _set_blend_func(self, instruction):
        '''Controller for the Gabor blending to the background color
        glBlendFunc(starting RGBA values, desired RGBA values)'''

        glBlendFunc(GL_ONE_MINUS_DST_ALPHA, GL_SRC_ALPHA)

    def _reset_blend_func(self, instruction):
        '''Reset of the Gabor blending properties for creation of new stimuli
        glBlendFunc(starting RGBA values, desired RGBA values)'''

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


if __name__ == '__main__':

    from .experiment import Experiment
    from .state import UntilDone, Wait, Parallel, Serial
    from .keyboard import KeyPress
    from .video import Label

    exp = Experiment(background_color="#4F33FF")

    g = Grating(width=250, height=250, contrast=0.1)
    with UntilDone():
        KeyPress()
        g.update(bottom=exp.screen.center)
        KeyPress()

    g = Grating(width=500, height=500, envelope='Gaussian', frequency=75,
                phase=11.0, color_one='blue', color_two='red', contrast=0.25)
    with UntilDone():
        KeyPress()
        g.update(bottom=exp.screen.center)
        KeyPress()

    with Parallel():
        g = Grating(width=256, height=256, frequency=20,
                    envelope='Circular', std_dev=7.5,
                    contrast=0.75,
                    color_one='green', color_two='orange')
        lbl = Label(text='Grating!', bottom=g.top)
    with UntilDone():
        # kp = KeyPress()
        with Parallel():
            g.slide(phase=-8 * math.pi, frequency=10.,
                    bottom=exp.screen.bottom,
                    duration=6.)
            g.slide(rotate=90, duration=2.0)
            with Serial():
                Wait(2.0)
                lbl.slide(top=g.bottom, duration=4.)

    with Parallel():
        g = Grating(width=1000, height=1000, frequency=10, envelope='Linear',
                    std_dev=20, contrast=0.4,
                    color_one='blue', color_two='red')
        lbl = Label(text='Grating!', bottom=g.top)
    with UntilDone():
        kp = KeyPress()
        with Parallel():
            g.slide(phase=-8 * math.pi, frequency=10.,
                    left=exp.screen.left,
                    duration=6.)
            g.slide(rotate=90, duration=2.0)
            with Serial():
                Wait(2.0)
                lbl.slide(top=g.bottom, duration=4.)

    exp.run(trace=False)
