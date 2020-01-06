from smile.experiment import Experiment
from smile.state import Parallel, Wait, Serial, Meanwhile, UntilDone, Loop
from smile.audio import Beep, SoundFile, init_audio_server
import os

init_audio_server(sr=44100, nchnls=2, buffersize=256, duplex=0,
                      audio='portaudio', jackname='pyo',
                      input_device=None, output_device=None)

exp = Experiment()

Wait(1.0)
with Loop([440, 500, 600, 880]) as l:
    Beep(freq=l.current, volume=0.4, duration=1.0)

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
SoundFile(os.path.join("..", "smile", "test_sound.wav"))
SoundFile(os.path.join("..", "smile", "test_sound.wav"), stop=1.0)
Wait(1.0)
SoundFile(os.path.join("..", "smile", "test_sound.wav"),
          loop=True, duration=3.0)
Wait(1.0)
SoundFile(os.path.join("..", "smile", "test_sound.wav"), start=0.5)
Wait(1.0)

exp.run()
