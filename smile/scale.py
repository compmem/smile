# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from ref import Ref
from kivy.metrics import dp

class Scale(object):
    """
    Utility to help scale depending on various screen sizes.

    Using a combination of Kivy's built in dp (density pixel) fuction and a
    scaling factor, we are able to scale stimulus in SMILE to any device.
    If you want to scale up or down to any monitor, you must set the scale_up
    and/or scale_down flags when defining your Experiment:

    ::

        exp = Experiment(scale_up=True, scale_down=True, scale_box=(600, 500))

    By doing so and wrapping all of your positional and sizing values your
    experiment will be scaled such that the scale_box fits completely on the
    screen you are running on.

    If you only care about keeping the stimulus the same size on every device,
    you should keep scale_up/down as False, and scale_box as None.

    Wrap all raw positional and size values with scale like so:

    ::

        scale(100)

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
