1# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
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
    """
    def __init__(self):
        self._scale_factor = 1.0
        self._scale_factor_ref = Ref.getattr(self, "_scale_factor")
        self.scale_down = False
        self.scale_up = False
        self._scale_box = [800, 600]

    def _set_scale_box(self, scale_box=None, scale_up, scale_down):
        self._scale_box = scale_box
        self.scale_up = scale_up
        self.scale_down = scale_down

    def _calc_scale_factor(self, width, height):

        if self.scale_down == True:
            if (dp(self._scale_box[1]) > height) & (dp(self._scale_box[0]) > width):
                if (height / dp(self._scale_box[1])) < (width / dp(self._scale_box[0])):
                    self._scale_factor = height / dp(self._scale_box[1])
                else:
                    self._scale_factor = height / dp(self._scale_box[1])
            elif dp(self._scale_box[1]) > height:
                self._scale_factor = height / dp(self._scale_box[1])
            elif dp(self._scale_box[0]) > width:
                self._scale_factor = width / dp(self._scale_box[0])

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
        return Ref(dp, val) * self._scale_factor_ref


# get global instance
scale = Scale()
