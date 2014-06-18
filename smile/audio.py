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

import pyo

# need a single global sound server
_ss = pyo.Server(sr=48000, nchnls=2, buffersize=512, duplex=1)
_ss.setOutputDevice(9)
_ss.setInputDevice(9)
_ss.boot()
#_ss = pyo.Server().boot()
_ss.start()

class Beep(State):
    """
    State that can play a beep.
    """
    def __init__(self, duration=1.0, freq=400, 
                 fadein=.1, fadeout=.1, volume=.5,
                 interval=0, parent=None, 
                 save_log=True):
        # init the parent class
        super(Beep, self).__init__(interval=interval, parent=parent, 
                                   duration=val(duration), 
                                   save_log=save_log)

        # save the vars
        self.dur = duration
        self.freq = freq
        self.fadein = fadein
        self.fadeout = fadeout
        self.volume = volume
        self.playing = False

    def _enter(self):
        self.duration = val(self.dur)
        self._fader = pyo.Fader(fadein=val(self.fadein), fadeout=val(self.fadeout), 
                                dur=self.duration, mul=val(self.volume))
        self._sine = pyo.Sine(freq=val(self.freq), mul=self._fader).out()

    def _callback(self, dt):
        if not self.playing:
            self._fader.play()
            self.playing = True
        if now() >= self.state_time+self.duration:
            # we're done
            self.playing = False
            self.leave()


if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    from state import Parallel, Loop, Func, Wait

    exp = Experiment()

    Beep(freq=[400,500],volume=.1)
    Beep(freq=[500,400],volume=.1)
    Beep(freq=[700,200],volume=.1)

    Wait(1.0, stay_active=True)

    exp.run()
