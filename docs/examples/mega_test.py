from smile.common import *
from smile.video import ProgressBar, TextInput
exp = Experiment()
import smile
import os
######### PARALLEL LOOPING LABEL ##############################################
with Parallel():
    with Loop(100) as lp:
        t1lb1 = Label(text='0', center_x=exp.screen.center_x/2, duration=.1, font_size=(lp.i+1))
    with Loop(5):
        t1lb2 = Label(text='1', duration=2)
    with Loop(3):
        Wait(2)
        t1lb3 = Label(text='2', center_x=exp.screen.center_x*3/2, duration=1)

######### CONDITIONAL LOOP ####################################################

exp.counter = 0

with Loop(conditional=(exp.counter < 5)):
    Label(text='SHAZBOT SAYS : This hasn\'t been on the screen for 5 times',
          text_size=(300, None),duration=.5)
    Wait(.2)
    exp.counter+=1

######### FLIP TEST FRAMERATE #################################################

# set the dur and isi for each trial
trials = [{'dur':d,'isi':i}
          for d,i in zip([.005,.010,.020,.050,.100,.200,.500,1.0],
                         [.005,.010,.020,.050,.100,.200,.500,1.0])]

# add in a bunch of fast switches
trials = [{'dur':.005,'isi':.005}]*10 + trials


# double length, reverse, and repeat

trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)

Wait(1.0)
with Loop(trials) as trial:
    # wait the isi
    reset = Wait(trial.current['isi'])
    onstim = Rectangle(color='WHITE', duration=trial.current['dur'])
    ResetClock(onstim.appear_time['time'])
    Done(onstim)
    Log(name="Flip_Test_Framerate",
        reset=reset.start_time,
        on_done=onstim.disappear_time,
        on_draw=onstim.appear_time,
        dur=trial.current['dur'],
        isi=trial.current['isi'])

Wait(1.0)

######### BUTTONS #############################################################

words = ['Bob','Tom','Dom']


with ButtonPress():
    MouseCursor()
    a = Button(text='Choice A', center_x=exp.screen.center_x/2)
    b = Button(text='Choice B')
    c = Button(text='Choice C', center_x=exp.screen.center_x*3/2)


with Loop(words) as trial:
    Wait(.2)
    Label(text=trial.current, duration=4)
    with UntilDone():
        with ButtonPress(correct_resp='chA', duration=4) as bp:
            MouseCursor()
            Button(name='chA',text='Choice A', center_x=exp.screen.center_x/2)
            Button(name='chB',text='Choice B', center_x=exp.screen.center_x*3/2)
    Wait(.2)
    with If(bp.correct):
        Label(text=bp.pressed,color='GREEN',duration=1)
    with Else():
        Label(text=bp.pressed,color='RED',duration=1)

######### LOOP SERIAL PARALLEL WAIT(UNTIL) ####################################

with Loop(5):
    with Parallel():
        with Serial(blocking=False):
            a = Label(text='SHAZBOT', duration = 1)
            Wait(.5)
        with Serial():
            b = Wait(until=a.appear_time)
            c = Label(text='THIS WILL BE ON THE SCREEN AT THE SAME TIME', duration=1.5, center_y=exp.screen.center_y/2)
        d = Label(text='This too', duration=1, center_y=exp.screen.center_y*4/3)
    Wait(.5)
    Log(name="Loop_Serial_Wait_Until_Test",
        lb_a_appear=a.appear_time['time'],
        lb_d_appear=d.appear_time['time'],
        lb_c_appear=c.appear_time['time'],
        lb_a_disappear=a.disappear_time['time'],
        lb_d_disappear=d.disappear_time['time'],
        lb_c_disappear=c.disappear_time['time'],)

######### UNTILDONE WAIT JITTER LABEL #########################################

with Loop(3):
    t6lb = Label(text="SHAZZBOT")
    with UntilDone():
        t6W = Wait(jitter=1, duration=1)
    Wait(1)
    Log(name="Wait_Jitter_Test",
        wait_start=t6W.start_time,
        wait_end=t6W.end_time,
        label_appear=t6lb.appear_time['time'],
        label_disappear=t6lb.disappear_time['time'])

######### VIDEO TESTING STUFF #################################################

Video(source=os.path.join(os.path.dirname(smile.__file__), "test_video.mp4"), duration=4.0)

pb = ProgressBar(max=100)
with UntilDone():
    pb.slide(value=100, duration=5.0)

Image(source=os.path.join(os.path.dirname(smile.__file__), "face-smile.png"), duration=5.0)

text = """
.. _top:

Hello world
===========

This is an **emphasized text**, some ``interpreted text``.
And this is a reference to top_::

$ print("Hello world")

"""
RstDocument(text=text, duration=5.0, size=exp.screen.size)

with ButtonPress():
    button = Button(text="Click to continue", size=(exp.screen.width / 4,
                                                    exp.screen.height / 8))
    slider = Slider(min=exp.screen.left, max=exp.screen.right,
                    top=button.bottom, blocking=False)
    rect = Rectangle(color="purple", width=50, height=50,
                     center_top=exp.screen.left_top, blocking=False)
    rect.animate(center_x=lambda t, initial: slider.value, blocking=False)
    ti = TextInput(text="EDIT!", top=slider.bottom, blocking=False)
    MouseCursor()
label = Label(text=ti.text, duration=1.0, font_size=50, color="white")

Ellipse(color="white", width=100, height=100)
with UntilDone():
    with Parallel():
        BackgroundColor("blue", duration=1.0)
        with Serial():
            Wait(1.0)
            BackgroundColor("green", duration=1.0)
        with Serial():
            Wait(2.0)
            BackgroundColor("red", duration=1.0)
        with Serial():
            Wait(3.0)
            BackgroundColor("yellow", duration=1.0)

rect = Rectangle(color="purple", width=50, height=50)
with UntilDone():
    Wait(.2)
    rect.center = exp.screen.right_top
    Wait(.2)
    rect.center = exp.screen.right_bottom
    Wait(.2)
    rect.center = exp.screen.left_top
    #Screenshot()
    Wait(.2)
    #rect.center = exp.screen.left_bottom
    rect.update(center=exp.screen.left_bottom, color="yellow")
    Wait(.2)
    #rect.center = exp.screen.center
    rect.update(center=exp.screen.center, color="purple")
    Wait(.2)
    rect.slide(center=exp.screen.right_top, duration=.2)
    rect.slide(center=exp.screen.right_bottom, duration=.2)
    rect.slide(center=exp.screen.left_top, duration=.2)
    rect.slide(center=exp.screen.left_bottom, duration=.2)
    rect.slide(center=exp.screen.center, duration=.2)
bez = Bezier(segments=200, color="yellow", loop=True,
             points=[0, 0, 200, 200, 200, 100, 100, 200, 500, 500])
with UntilDone():
    bez.slide(points=[200, 200, 0, 0, 500, 500, 200, 100, 100, 200],
              color="blue", duration=1.0)
    bez.slide(points=[500, 0, 0, 500, 600, 200, 100, 600, 300, 300],
              color="white", duration=1.0)
with BoxLayout(width=500, height=500, top=exp.screen.top, duration=4.0):
    rect = Rectangle(color=(1.0, 0.0, 0.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=1.0)
    Rectangle(color="#00FF00", pos=(0, 0), size_hint=(1, 1), duration=2.0)
    Rectangle(color=(0.0, 0.0, 1.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=1.0)
    rect.slide(color=(1.0, 1.0, 1.0, 1.0), duration=1.0)
img = Image(source=os.path.join(os.path.dirname(smile.__file__), "face-smile.png"), size=(10, 10), allow_stretch=True,
            keep_ratio=False, mipmap=True)
with UntilDone():
    img.slide(size=(100, 200), duration=1.0)

######### AUDIO BEEP RECORD PLAY ##############################################
from smile.audio import SoundFile, Beep, RecordSoundFile
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
SoundFile(os.path.join(os.path.dirname(smile.__file__), "test_sound.wav"))
SoundFile(os.path.join(os.path.dirname(smile.__file__), "test_sound.wav"), stop=1.0)
Wait(1.0)
SoundFile(os.path.join(os.path.dirname(smile.__file__), "test_sound.wav"), loop=True, duration=3.0)
Wait(1.0)
SoundFile(os.path.join(os.path.dirname(smile.__file__), "test_sound.wav"), start=0.5)
rec = RecordSoundFile(filename='Test_rec.mp3')
with UntilDone():
    with Loop(3):
        Beep(freq=[1000, 500, 600], volume=0.1, duration=1.0)
        Beep(freq=880, volume=0.1, duration=1.0)
Wait(1.0)
SoundFile(rec.filename)
Wait(1.0)
################### RUN IT ####################################################
exp.run()


