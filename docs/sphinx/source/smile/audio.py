#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import os
import time

from state import Wait
from clock import clock

# add in system site-packages if necessary
try:
    import pyo
except ImportError:
    import sys
    if sys.platform == 'darwin':
        os_sp_dir = '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages'
    elif sys.platform.startswith('win'):
        os_sp_dir = 'C:\Python27\Lib\site-packages'
    else:
        raise ImportError("Could not import pyo and no special pyo path for "
                          "this platform (%s)." % sys.platform)
    if not os_sp_dir in sys.path:
        sys.path.append(os_sp_dir)
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


#TODO: compensate for buffer lag where possible?

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

def default_init_audio_server():
    if _pyo_server is None:
        # try and init it with defaults
        # print some warning
        init_audio_server()


class Beep(Wait):
    def __init__(self, duration=None, freq=400, fadein=0.05, fadeout=0.05,
                 volume=0.5, parent=None, save_log=True, name=None, blocking=True):
        super(Beep, self).__init__(parent=parent, 
                                   duration=duration, 
                                   save_log=save_log,
                                   name=name,
                                   blocking=blocking)

        self._init_freq = freq
        self._init_fadein = fadein
        self._init_fadeout = fadeout
        self._init_volume = volume
        self._sound_start_time = None
        self.__fader = None
        self.__sine = None

        # set the log attrs
        self.log_attrs.extend(['freq', 'volume', 'fadein', 'fadeout',
                               'sound_start_time'])

    def _enter(self):
        super(Beep, self)._enter()
        default_init_audio_server()
        self._sound_start_time = None
        if self._start_time == self._end_time:
            self.__fader = None
            self.__sine = None
        else:
            self.__fader = pyo.Fader(fadein=self._fadein,
                                     fadeout=self._fadeout,
                                     mul=self._volume)
            self.__sine = pyo.Sine(freq=self._freq, mul=self.__fader)
            clock.schedule(self._start_sound, event_time=self._start_time)
            if self._end_time is not None:
                clock.schedule(self._stop_sound,
                               event_time=self._end_time-self._fadeout)

    def _start_sound(self):
        self.__sine.out()
        self.__fader.play()
        self._sound_start_time = clock.now()

    def _stop_sound(self):
        if self.__fader is not None:
            self.__fader.stop()
            self.__fader = None
            self.__sine = None

    def cancel(self, cancel_time):
        super(Beep, self).cancel(cancel_time)
        clock.unschedule(self._stop_sound)
        clock.schedule(self._stop_sound,
                       event_time=self._end_time-self._fadeout)


class SoundFile(Wait):
    def __init__(self, filename, volume=0.5, start=0.0, stop=None,
                 duration=None, loop=False, parent=None, save_log=True,
                 name=None, blocking=True):
        super(SoundFile, self).__init__(parent=parent,
                                        duration=duration,
                                        save_log=save_log,
                                        name=name,
                                        blocking=blocking)
        self._init_filename = filename
        self._init_volume = volume
        self._init_start = start
        self._init_stop = stop
        self._init_loop = loop
        self._sound_start_time = None

        # set the log attrs
        self.log_attrs.extend(['filename', 'volume', 'start', 'stop', 'loop',
                               'sound_start_time'])

    def _enter(self):
        super(SoundFile, self)._enter()
        default_init_audio_server()
        self._sound_start_time = None

        # init the sound table (two steps to get mono in both speakers)
        sndtab = pyo.SndTable(initchnls=_pyo_server.getNchnls())
        sndtab.setSound(path=self._filename, start=self._start,
                        stop=self._stop)

        # set the end time
        if not self._loop:
            self.cancel(self._start_time + sndtab.getDur())

        # read in sound info
        self.__snd = pyo.TableRead(sndtab, freq=sndtab.getRate(),
                                   loop=self._loop,
                                   mul=self._volume)
        if self.__snd is None:
            raise RuntimeError("Could not load sound file: %r" %
                               self._filename)

        # schedule playing the sound
        clock.schedule(self._start_sound, event_time=self._start_time)

        # schedule stopping the sound
        if self._end_time is not None:
                clock.schedule(self._stop_sound, event_time=self._end_time)

    def _start_sound(self):
        self.__snd.out()
        self._sound_start_time = clock.now()

    def _stop_sound(self):
        if self.__snd is not None:
            self.__snd.stop()
            self.__snd = None

    def cancel(self, cancel_time):
        super(SoundFile, self).cancel(cancel_time)
        clock.unschedule(self._stop_sound)
        clock.schedule(self._stop_sound, event_time=self._end_time)


class RecordSoundFile(Wait):
    def __init__(self, duration=None, filename=None, parent=None,
                 save_log=True, name=None, blocking=True):
        # init the parent class
        super(RecordSoundFile, self).__init__(parent=parent,
                                              duration=duration,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)

        self._init_filename = filename
        self._rec_start = None
        self.__rec = None

        # set the log attrs
        self.log_attrs.extend(['filename', 'filepath', 'rec_start'])

    def _enter(self):
        super(RecordSoundFile, self)._enter()
        default_init_audio_server()
        if self._filename is None:
            self._filename = self._exp.reserve_data_filename(
                "audio_%s" % self._name, "wav", use_timestamp=True)
        clock.schedule(self._start_recording, event_time=self._start_time)
        if self._end_time is not None:
            clock.schedule(self._stop_recording, event_time=self._end_time)

    def _start_recording(self):
        self.__rec = pyo.Record(
            pyo.Input(), filename=self._filename, chnls=2, fileformat=0,
            sampletype=1, buffering=16)
        self._rec_start = clock.now()

    def _stop_recording(self):
        if self.__rec is not None:
            self.__rec.stop()
            self.__rec = None

    def cancel(self, cancel_time):
        super(RecordSoundFile, self).cancel(cancel_time)
        clock.unschedule(self._stop_recording)
        clock.schedule(self._stop_recording, event_time=self._end_time)


if __name__ == '__main__':

    from experiment import Experiment
    from state import Parallel, Wait, Serial, Meanwhile, UntilDone, Loop

    exp = Experiment()

    Wait(1.0)
    Beep(freq=[440, 500, 600], volume=0.1, duration=1.0)
    Beep(freq=880, volume=0.1, duration=1.0)
    with Parallel():
        Beep(freq=440, volume=0.1, duration=2.0)
        with Serial():
            Wait(1.0)
            Beep(freq=880, volume=0.1, duration=2.0)
    Wait(1.0)
    with Meanwhile():
        Beep(freq=500, volume=0.1)
    Beep(freq=900, volume=0.1, duration=1.0)
    SoundFile("test_sound.wav")
    SoundFile("test_sound.wav", stop=1.0)
    Wait(1.0)
    SoundFile("test_sound.wav", loop=True, duration=3.0)
    Wait(1.0)
    SoundFile("test_sound.wav", start=0.5)
    rec = RecordSoundFile()
    with UntilDone():
        with Loop(3):
            Beep(freq=[440, 500, 600], volume=0.1, duration=1.0)
            Beep(freq=880, volume=0.1, duration=1.0)
    Wait(1.0)
    SoundFile(rec.filename)
    Wait(1.0)

    exp.run()
