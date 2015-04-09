#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import os

from state import State, Wait, Serial
from state import schedule_delayed_interval, schedule_delayed
from ref import Ref, val

# get the last instance of the experiment class
from experiment import Experiment, now, event_time

from pyglet import clock
import pyglet

# add in system site-packages if necessary
try:
    import pyo
except ImportError:
    import sys
    if sys.platform == 'darwin':
        os_sp_dir = '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages'
    elif sys.platform.startswith('win'):
        os_sp_dir = 'C:\Python27\Lib\site-packages'
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
    
    Parameters
    ----------
    duration : {1.0, float}
        Duration of the state.
    freq: {400, int}
    	Frequency of the beep in Hz 
    fadein: {.05, float}
    	Fade-in time of the beep
    fadeout: {.05, float}
    	Fade-out time of the beep
    volume: {.5, float}
    	Volume of the beep
    parent: object
    	The parent state
        save_log: bool
    If set to 'True,' details about the Beep state will be automatically saved 
        in the log files.
    
    Example
    -------
    Beep(duration = 2.0, freq = 500, fadein = 0.1, fadeout = 0.2, volume = .5)
    The state will play a beep at 500 Hz at 50% volume with 0.1 seconds fade-in, 
    2.0 second duration, and 0.2 second fade-out
    
    """
    def __init__(self, duration=1.0, freq=400, 
                 fadein=.05, fadeout=.05, volume=.5,
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

        self.sound_start = None

        # set the log attrs
        self.log_attrs.extend(['freq', 'volume', 'fadein', 'fadeout', 'sound_start'])

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
        self.sound_start = event_time(now())


class RecordSoundFile(State):
    """
    State that records microphone input to an audio file (WAV)
    
    Parameters
    ----------
    duration: {0, float}
        Length of time to record the audio file
    filename: str
        Name of the audio file to create in the log directory.  If None, a
        unique name is automatically generated each time the state is executed.
    parent: object
        The parent state

    Example
    -------
    RecordSoundFile(10.0)
        Record audio for ten seconds.
    
    """
    def __init__(self, duration, filename=None, parent=None):
        # init the parent class
        super(RecordSoundFile, self).__init__(interval=0, parent=parent,
                                              duration=val(duration))

        self.filename = filename
        self.generate_filename = filename is None

        # set the log attrs
        self.log_attrs.extend(['filename', 'duration', 'rec_start'])

    def _enter(self):
        if _pyo_server is None:
            # try and init it with defaults
            # print some warning
            init_audio_server()
        if self.generate_filename:
            self.filename = self.exp.reserve_data_filename("rec", "wav")
            #TODO: when state names are implemented, use state name for file title
        self.filepath = os.path.join(self.exp.subj_dir, val(self.filename))

    def _callback(self, dt):
        self._rec = pyo.Record(
            pyo.Input(), filename=self.filepath, chnls=2, fileformat=0,
            sampletype=1, buffering=16)
        self.rec_start = event_time(now())
        pyo.Clean_objects(self.duration, self._rec).start()
        # eventually use triggers for more accurate timing


class SoundFile(State):
    """
    State that can play audio files
    
    Parameters
    ----------
    sound_file: file object
    	The filepath to the sound file to be played 
    start:  {0.0, float}
    	The start time for the audio file to be played
    stop: {None, float}
    	The stop time for the audio file; defaults to playing the entire file
    volume: {.5, float}
    	The volume at which to play the audio file
    loop: {False, bool}
    	Loops the audio file after it finishes
    duration: {0, float}
    	Length of time to play the audio file 
    parent: object
    The parent state
        save_log: bool
    If set to 'True,' details about the Beep state will be automatically saved 
        in the log files.
    
    Examples
    --------
    SoundFile(sound_file = 'some/file/path')
    	A sound file at the designated file path will be played at 50% volume.
    
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

        self.sound_start = None

        # set the log attrs
        self.log_attrs.extend(['sound_file', 'volume', 'start', 'stop', 
                               'loop', 'sound_start'])

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
        self.sound_start = event_time(now())
        # eventually use triggers for more accurate timing


if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    from state import Parallel, Loop, Func, Wait, ResetClock

    init_audio_server()

    exp = Experiment()

    Beep(freq=[300,700],volume=.1)
    Beep(freq=[500,500],volume=.1)
    with Parallel():
        Beep(freq=[700,300],volume=.1)
        #SoundFile('kongas.wav',
        #      stop=5.0, volume=.1)
        with Serial():
            Wait(1.0)
            Beep(freq=[400,400],volume=.1)
        with Serial():
            Wait(2.0)
            Beep(freq=[300,300],volume=.1)
        rec_snd = RecordSoundFile(8.0)
        RecordSoundFile(4.0, "test.aiff")
    SoundFile(Ref(rec_snd, "filepath"))

    Wait(1.0, stay_active=True)

    exp.run()
