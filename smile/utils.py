#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import math
import wave
import struct
import random
from itertools import *
from io import StringIO

def rindex(lst, item):
    try:
        return dropwhile(lambda x: lst[x] != item, reversed(range(len(lst)))).next()
    except StopIteration:
        raise ValueError("rindex(lst, item): item not in list")

def get_class_name(obj):
    name = str(obj.__class__)[8:-2].split('.')[-1]
    mem_id = str(id(obj))
    uname = name + "_" + mem_id
    return name,uname


#
# some audio utils adapted from:
# http://zacharydenton.com/generate-audio-with-python/
#

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

def sine_wave(frequency=440.0, framerate=44100, amplitude=0.5,
        skip_frame=0):
    '''
    Generate a sine wave at a given frequency of infinite length.
    '''
    if amplitude > 1.0: amplitude = 1.0
    if amplitude < 0.0: amplitude = 0.0
    for i in count(skip_frame):
        sine = math.sin(2.0 * math.pi * float(frequency) * 
                        (float(i) / float(framerate)))
        yield float(amplitude) * sine

def square_wave(frequency=440.0, framerate=44100, amplitude=0.5):
    for s in sine_wave(frequency, framerate, amplitude):
        if s > 0:
            yield amplitude
        elif s < 0:
            yield -amplitude
        else:
            yield 0.0

def damped_wave(frequency=440.0, framerate=44100, amplitude=0.5, length=44100):
    if amplitude > 1.0: amplitude = 1.0
    if amplitude < 0.0: amplitude = 0.0
    return (math.exp(-(float(i%length)/float(framerate))) * s 
            for i, s in enumerate(sine_wave(frequency, framerate, amplitude)))

def white_noise(amplitude=0.5):
    '''
    Generate random samples.
    '''
    return (float(amplitude) * random.uniform(-1, 1) for i in count(0))

def compute_samples(channels, nsamples=None):
    '''
    create a generator which computes the samples.

    essentially it creates a sequence of the sum of each function in the channel
    at each sample in the file for each channel.
    '''
    return islice(izip(*(imap(sum, izip(*channel)) for channel in channels)), nsamples)

def write_wavefile(f, samples, nframes=None, nchannels=2, 
                   sampwidth=2, framerate=44100, bufsize=2048):
    "Write samples to a wavefile."

    # next line breaks it, leaving at None
    #if nframes is None:
    #    nframes = -1

    w = wave.open(f, 'w')
    w.setparams((nchannels, sampwidth, framerate, nframes, 'NONE', 'not compressed'))

    max_amplitude = float(int((2 ** (sampwidth * 8)) / 2) - 1)

    # split the samples into chunks (to reduce memory consumption and improve performance)
    for chunk in grouper(bufsize, samples):
        frames = ''.join(''.join(struct.pack('h', int(max_amplitude * sample)) 
                                 for sample in channels) for channels in chunk 
                         if channels is not None)
        w.writeframesraw(frames)
    
    w.close()

def write_wavebuf(samples, nframes=None, nchannels=2, 
                  sampwidth=2, framerate=44100, bufsize=2048):
    """Write samples to a wave buffer."""
    buf = StringIO()
    write_wavefile(buf, samples)
    buf.seek(0)
    return buf

