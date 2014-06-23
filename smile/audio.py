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
_pyo_server = None
# if False:
#     _pyo_server = pyo.Server(sr=48000, nchnls=2, buffersize=512, duplex=1)
#     _pyo_server.setOutputDevice(9)
#     _pyo_server.setInputDevice(9)
#     _pyo_server.boot()
# else:
#     _pyo_server = pyo.Server().boot()
# _pyo_server.start()


def init_audio_server(sr=44100, nchnls=2, buffersize=256, duplex=1, 
                      audio='portaudio', jackname='pyo', 
                      input_device=None, output_device=None):
    # grab the global server
    global _pyo_server

    # eventually read defaults from a config file

    # set up the server
    if _pyo_server is None:
        # init first time
        _pyo_server = pyo.Server(sr=sr, nchnls=nchnls, buffersize=buffersize,
                                 duplex=duplex, audio=audio, jackname=jackname)
    else:
        # stop and reinit
        _pyo_server.stop()
        _pyo_server.reinit(sr=sr, nchnls=nchnls, buffersize=buffersize,
                           duplex=duplex, audio=audio, jackname=jackname)

    # see if change in/out
    if input_device:
        _pyo_server.setInputDevice(input_device)
    if output_device:
        _pyo_server.setOutputDevice(output_device)

    # boot it and start it
    _pyo_server.boot()
    _pyo_server.start()

    return _pyo_server


class Beep(State):
    """
    State that can play a beep.
    """
    def __init__(self, duration=1.0, freq=400, 
                 fadein=.1, fadeout=.1, volume=.5,
                 parent=None, 
                 save_log=True):
        # init the parent class
        super(Beep, self).__init__(interval=0, parent=parent, 
                                   duration=val(duration), 
                                   save_log=save_log)

        # save the vars
        self.dur = duration
        self.freq = freq
        self.fadein = fadein
        self.fadeout = fadeout
        self.volume = volume

        # set the log attrs
        self.log_attrs.extend(['freq', 'volume', 'fadein', 'fadeout'])

    def _enter(self):
        if _pyo_server is None:
            # try and init it with defaults
            # print some warning
            init_audio_server()

        # process the vars
        self.duration = val(self.dur)
        self._fader = pyo.Fader(fadein=val(self.fadein), fadeout=val(self.fadeout), 
                                dur=self.duration, mul=val(self.volume))
        self._sine = pyo.Sine(freq=val(self.freq), mul=self._fader).out()

    def _callback(self, dt):
        self._fader.play()


class SoundFile(State):
    """
    State that can play a beep.
    """
    def __init__(self, sound_file, start=0, stop=None, volume=.5, loop=False,
                 duration=0, parent=None, save_log=True):
        # init the parent class
        super(SoundFile, self).__init__(interval=0, parent=parent, 
                                    duration=val(duration), 
                                    save_log=save_log)

        # save the vars
        self.sound_file = sound_file
        self.start = start
        self.stop = stop
        self.volume = volume
        self.duration = duration
        self.loop = loop

        # set the log attrs
        self.log_attrs.extend(['sound_file', 'volume', 'start', 'stop', 'loop'])

    def _enter(self):
        if _pyo_server is None:
            # try and init it with defaults
            # print some warning
            init_audio_server()

        # process the vars
        sound_file = val(self.sound_file)
        start = val(self.start)
        stop = val(self.stop)

        # init the sound table (two steps to get mono in both speakers)
        sndtab = pyo.SndTable(initchnls=_pyo_server.getNchnls())
        sndtab.setSound(path=sound_file, start=start, stop=stop)

        # set the duration if not looping
        if val(self.loop):
            # set callback for stopping sound
            raise NotImplemented("Looping sounds is currently not supported.")
        else:
            self.duration = sndtab.getDur()

        # read in sound info
        self._snd = pyo.TableRead(sndtab, freq=sndtab.getRate(),
                                  loop=val(self.loop), 
                                  mul=val(self.volume))

    def _callback(self, dt):
        # play the sound
        self._snd.out()
        # eventually use triggers for more accurate timing


if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    from state import Parallel, Loop, Func, Wait, ResetClock

    init_audio_server()

    exp = Experiment()

    Beep(freq=[300,700],volume=.1)
    Beep(freq=[500,500],volume=.1)
    # with Parallel():
    #     Beep(freq=[700,300],volume=.1)
    #     SoundFile('~/code/pyo-read-only/examples/snds/flute.aif',
    #           stop=3.0, volume=.1)

    Wait(1.0, stay_active=True)

    exp.run()
