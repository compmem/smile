# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .ref import Ref
from kivy.metrics import dp

class Scale(object):
    """
    Utility to help scale depending on various screen sizes.

    By default, using **scale** will pass any number through kivy's built in dp
    function which converts your number into density pixels. If your display
    device has a density of 1, then the number will not change, but if your
    density is 2, your number will be doubled inorder to maintain the same
    size independent of density. The other thing this function can do is scale
    up and scale down to differening screen sizes. In order to tell smile to do
    this, you must set the scale_up and/or scale_down flags, and define a
    scale_box, when initializing your Experiment:

    ::

        exp = Experiment(scale_up=True, scale_down=True, scale_box=(600, 500))

    This tells smile to expand or shrink all numbers passed through scale by a
    scaling factor that would allow the scale_box to fit within whatever
    monitor resolution you are using.

    Wrap all raw positional and size values with scale like so:

    ::

        scale(100)

    As an example: lets say you were wanting to write an experiment that would be
    run on a large monitor, 1600x900, but also a phone, 1920x1080, with a pixel
    density that was 4 time as much your monitor. Using just dp, the 600x600
    stimulus you would try to display would be 2400x2400 on the phone. That
    stimulus would be way to big to fit on a 1920x1080 screen, so you need to
    set scale_down to True, and set your scale box to be something appropriate.

    For this example, lets say our scale_box is 800x800 so that we have 200
    pixels of extra room around the stimulus. The limiting factor here is the
    height of the phone screen, so we calculate our scaling factor based on
    that. dp(800) would end up being 3200 density pixels. To calculated the
    scaling factor we just take the height of the screen and divide it by
    the dp'd height of the scale_box. that would be 0.3375. So now, after
    converting all of our numbers to density pixels, we multiply that by a
    scaling factor of 0.3375.

    ::

        2400*0.3375 = 810

    Our stimulus would be 810x810 density pixels in size, and fit perfextly in
    the center of our phone device. But the end user doesn't have to worry about
    any of this calculations if they set the scale_box to 800x800, scale_down
    to True, and wrapped the height and width of the stimulus with scale as
    scale(600).

    """
    def __init__(self):
        self._scale_factor = 1.0
        self._scale_factor_ref = Ref.getattr(self, "_scale_factor")
        self.scale_down = False
        self.scale_up = False
        self._scale_box = None

    def _set_scale_box(self, scale_up=False, scale_down=False, scale_box=None):
        self._scale_box = scale_box
        self.scale_up = scale_up
        self.scale_down = scale_down

    def _calc_scale_factor(self, width, height):
        # If they offered a scale box
        if self._scale_box is not None:
            # If scale_down is True then check to see if you need to scale down
            if self.scale_down == True:
                # If both the density pixel height and width are bigger than the
                # height and width of the screen, than check which one we
                # should scale down.
                if (dp(self._scale_box[1]) > height) & (dp(self._scale_box[0]) > width):
                    if (height / dp(self._scale_box[1])) < (width / dp(self._scale_box[0])):
                        self._scale_factor = height / dp(self._scale_box[1])
                    else:
                        self._scale_factor = height / dp(self._scale_box[1])
                elif dp(self._scale_box[1]) > height:
                    self._scale_factor = height / dp(self._scale_box[1])
                elif dp(self._scale_box[0]) > width:
                    self._scale_factor = width / dp(self._scale_box[0])
            # If scale_up is True
            if self.scale_up == True:
                if (dp(self._scale_box[1]) < height) & (dp(self._scale_box[0]) < width):
                    if (height / dp(self._scale_box[1])) > (width / dp(self._scale_box[0])):
                        self._scale_factor = height / dp(self._scale_box[1])
                    else:
                        self._scale_factor = height / dp(self._scale_box[1])
                elif dp(self._scale_box[1]) < height:
                    self._scale_factor = height / dp(self._scale_box[1])
                elif dp(self._scale_box[0]) < width:
                    self._scale_factor = width / dp(self._scale_box[1])

    def __call__(self, val):
        # Wrap the value in a ref. scale_factor is 1.0 by default, but we are
        # always trying to scale a dp value, not a raw pixel value.
        return Ref(dp, val) * self._scale_factor_ref


# get global instance
scale = Scale()