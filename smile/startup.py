# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from kivy_overrides import Config as KOConfig
import kivy_overrides as KO
from state import Subroutine, Parallel, Serial, Loop, If, Else, Elif, \
                  UntilDone, ResetClock, Func, Wait, Debug
from video import Rectangle, ProgressBar, Label, UpdateWidget, \
                  CheckBox, TextInput, ButtonPress, Button, Image
from keyboard import KeyPress
from ref import Ref
from mouse import MouseCursor
from scale import scale as s

import os


# general config for splash and settings
LOGO_IMG = "logo.png"
SMILE_IMG = "face-smile.png"
LOGO_WIDTH = 639
LOGO_HEIGHT = 100
INFO_WIDTH = 500
INFO_HEIGHT = 600
INFO_OUTLINE_COLOR = [51./255., 107./255., 135./255.]
INFO_COLOR = [144./255., 175./255., 197./255.]
INFO_BUTTON_WIDTH = 200
INFO_BUTTON_HEIGHT = 50
INTRO_WIDTH = 700
INTRO_HEIGHT = 500
TEXT_INPUT_WIDTH = 300
TEXT_INPUT_HEIGHT = 50
INFO_FONT_SIZE = 30
SSI_FONT_SIZE = 40
CHECK_HEIGHT = 25
CHECK_WIDTH = 25
LOCK_ON = "lock.png"
LOCK_OFF = "unlock.png"
LOCK_HEIGHT = 40
LOCK_WIDTH = 40



def set_flip_interval(fps):
    from experiment import Experiment
    exp = Experiment._last_instance()
    exp._app.flip_interval = 1./fps

@Subroutine
def FrameTest(self,
              num_flips=200,
              to_skip=5):

    Func(set_flip_interval, 200.)
    self.tot_flips = num_flips + to_skip
    self.diff_sum = 0.0
    self.last_flip = 0

    with Parallel():
        # BlockingFlips()
        config_window = Rectangle(height=s(INFO_HEIGHT) + s(20),
                                  width=s(INFO_WIDTH) + s(20),
                                  color=INFO_OUTLINE_COLOR)
        recin = Rectangle(height=s(INFO_HEIGHT),
                          width=s(INFO_WIDTH),
                          color=INFO_COLOR,
                          center_y=config_window.center_y)
        pb = ProgressBar(max=self.tot_flips, width=config_window.width*2/3,
                         height=s(50),
                         center_y=recin.center_y, center_x=recin.center_x)
        lbl = Label(text='???', top=pb.bottom, font_size=s(INFO_FONT_SIZE),
                    center_x=recin.center_x)
    with UntilDone():
        with Loop(self.tot_flips) as loop:
            # skip the first 5
            with Parallel():
                uw = UpdateWidget(pb, value=loop.i+1)
                with If(self.diff_sum > 0.0):
                    UpdateWidget(lbl,
                                 text=Ref('{:5.2f}'.format,
                                          (loop.i-to_skip)/self.diff_sum))
            with If(loop.i >= to_skip):
                self.diff_sum = self.diff_sum + \
                                (uw.appear_time['time'] - self.last_flip)
            self.last_flip = uw.appear_time['time']
            ResetClock(self.last_flip)
    self.framerate = lbl.text


def calc_density(height, width, heightcm, widthcm):
    return (((height/heightcm)+(width/widthcm)) * 2.54 / 2.0) / 96.

@Subroutine
def ConfigWindow(self):

    resy = Func(KO._get_config)

    self.params = resy.result
    self.canceled = True
    self.keep_looping = True

    self.frameText = Ref(str, self.params['frame_rate'])
    self.density = Ref(str, self.params['density'])
    with Loop(conditional=self.keep_looping):
        with Parallel():
            MouseCursor()
            config_window = Rectangle(height=s(INFO_HEIGHT) + s(20),
                                      width=s(INFO_WIDTH) + s(20),
                                      color=INFO_OUTLINE_COLOR)
            recin = Rectangle(height=s(INFO_HEIGHT),
                              width=s(INFO_WIDTH),
                              color=INFO_COLOR,
                              center_y=config_window.center_y)
            title = Label(text="SMILE Settings",
                          font_size=s(INFO_FONT_SIZE),
                          top=config_window.top - s(50))

            timeInput = TextInput(text=self.frameText,
                                  font_size=s(INFO_FONT_SIZE),
                                  width=s(TEXT_INPUT_WIDTH)/3.,
                                  height=s(TEXT_INPUT_HEIGHT),
                                  left=recin.left + s(20),
                                  top=title.bottom - s(40),
                                  multiline=False)
            timeLabel = Label(text="Framerate",
                              center_y=timeInput.center_y,
                              left=timeInput.right + s(10),
                              font_size=s(INFO_FONT_SIZE))
            timing_button = Button(name="timing", text="Test",
                                   font_size=s(INFO_FONT_SIZE),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=s(INFO_BUTTON_WIDTH),
                                   background_color=INFO_OUTLINE_COLOR,
                                   background_normal="",
                                   center_y=timeLabel.center_y,
                                   left=timeLabel.right + s(20))

            densityLabel = Label(text="Density:",
                                 top=timeInput.bottom - s(40),
                                 left=recin.left + s(20),
                                 font_size=s(INFO_FONT_SIZE))
            densityText = TextInput(text=self.density,
                                    font_size=s(INFO_FONT_SIZE),
                                    width=s(TEXT_INPUT_WIDTH)/3.,
                                    height=s(TEXT_INPUT_HEIGHT),
                                    left=densityLabel.right + s(20),
                                    center_y=densityLabel.center_y,
                                    multiline=False)
            wcmLabel = Label(text="Width (cm):",
                             top=densityLabel.bottom - s(20),
                             left=recin.left + s(20),
                             font_size=s(INFO_FONT_SIZE))
            hcmLabel = Label(text="Height (cm):",
                             top=wcmLabel.bottom - s(20),
                             left=recin.left + s(20),
                             font_size=s(INFO_FONT_SIZE))
            wcmText = TextInput(font_size=s(INFO_FONT_SIZE),
                                width=s(TEXT_INPUT_WIDTH)/4.,
                                height=s(TEXT_INPUT_HEIGHT),
                                left=Ref(max,
                                         wcmLabel.right,
                                         hcmLabel.right) + s(10),
                                center_y=wcmLabel.center_y,
                                multiline=False)
            hcmText = TextInput(font_size=s(INFO_FONT_SIZE),
                                width=s(TEXT_INPUT_WIDTH)/4.,
                                height=s(TEXT_INPUT_HEIGHT),
                                left=Ref(max,
                                         wcmLabel.right,
                                         hcmLabel.right) + s(10),
                                center_y=hcmLabel.center_y,
                                multiline=False)
            density_button = Button(name="calc_den", text="Calc Density",
                                    font_size=s(INFO_FONT_SIZE),
                                    height=s(INFO_BUTTON_HEIGHT),
                                    width=s(INFO_BUTTON_WIDTH),
                                    background_color=INFO_OUTLINE_COLOR,
                                    background_normal="",
                                    center_y=(hcmText.center_y + wcmText.center_y)/2.,
                                    right=timing_button.right)

            # CONTINUE BUTTONS
            cancel_button = Button(text="Cancel", name="cancel",
                                   bottom=recin.bottom + s(20),
                                   left=recin.left + s(20),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=s(INFO_BUTTON_WIDTH),
                                   font_size=s(INFO_FONT_SIZE),
                                   background_color=INFO_OUTLINE_COLOR,
                                   background_normal="")
            app_button = Button(text="Apply", name="apply",
                                bottom=recin.bottom + s(20),
                                right=recin.right - s(20),
                                font_size=s(INFO_FONT_SIZE),
                                height=s(INFO_BUTTON_HEIGHT),
                                width=s(INFO_BUTTON_WIDTH),
                                background_color=INFO_OUTLINE_COLOR,
                                background_normal="")

        with UntilDone():
            bp = ButtonPress(buttons=[cancel_button,
                                      app_button,
                                      timing_button,
                                      density_button])
            Wait(.25)

        with If(bp.pressed == "apply"):
            self.exp.flip_interval = 1./Ref(float, timeInput.text)
            self.framerate = Ref(float, timeInput.text)
            with If(densityText.text == self.params['density']):
                self.density = None
            with Else():
                self.density = densityText.text
            self.keep_looping = False

            Func(set_flip_interval, self.framerate)

            Func(KO._set_config, framerate=self.framerate,
                 density=self.density)
        with Elif(bp.pressed == "calc_den"):
            cd = Func(calc_density, height=self.exp.screen.height,
                      width=self.exp.screen.width,
                      heightcm=Ref(float, hcmText.text),
                      widthcm=Ref(float, wcmText.text))
            self.density = Ref(str,cd.result)
        with Elif(bp.pressed == "timing"):
            ft = FrameTest()
            self.frameText = ft.framerate
        with Else():
            self.keep_looping = False


@Subroutine
def Splash(self, Touch=False):
    if Touch:
        cont_key_str = "the screen"
    else:
        cont_key_str = "any key"

    with Parallel():
        rout = Rectangle(width=s(INTRO_WIDTH) + s(20),
                         height=s(INTRO_HEIGHT) + s(20),
                         color=INFO_OUTLINE_COLOR)
        Rectangle(width=s(INTRO_WIDTH),
                  height=s(INTRO_HEIGHT),
                  color=INFO_COLOR)
        ssi = Image(source=os.path.join(os.path.dirname(__file__),
                                        LOGO_IMG),
                    allow_stretch=True,
                    width=s(LOGO_WIDTH),
                    height=s(LOGO_HEIGHT),
                    keep_ratio=False)
        sl = Label(text="SMILE",
                   halign="center", bottom=ssi.top + s(75),
                   font_size=s(SSI_FONT_SIZE)*2)
        Image(source=os.path.join(os.path.dirname(__file__),
                                  SMILE_IMG),
              allow_stretch=True,
              opacity=.5,
              right=sl.left - s(10),
              center_y=sl.center_y,
              width=sl.height,
              height=sl.height,
              keep_ratio=False)
        Image(source=os.path.join(os.path.dirname(__file__),
                                  SMILE_IMG),
              allow_stretch=True,
              opacity=.5,
              left=sl.right + s(10),
              center_y=sl.center_y,
              width=sl.height,
              height=sl.height,
              keep_ratio=False)
        Label(text="brought to you by the",
              halign="center", top=sl.bottom,
              font_size=s(SSI_FONT_SIZE))
        Label(text="UVA Computational Memory Lab\n\nPress %s to continue"%(cont_key_str),
              top=ssi.bottom,
              multiline=True, halign="center",
              font_size=s(SSI_FONT_SIZE))
    with UntilDone():
        with Parallel():
            kp = KeyPress(blocking=False)
            with Serial(blocking=False):
                with ButtonPress() as bp:
                    Button(size=self.exp.screen.size, text="", left=0,
                           bottom=0, background_color=(0, 0, 0, 0))


@Subroutine
def InputSubject(self, exp_title="DefaultExperiment"):
    KOConfig.adddefaultsection(exp_title)

    # get the config for whether we've locked the subject
    if KOConfig.getdefault(exp_title, "LOCK_SUBJ_PASSWORD", "") != "":
        self.text = KOConfig.getdefault(exp_title,
                                       "LOCK_SUBJ",
                                       "subj000")
        self.lock_password = KOConfig.getdefault(exp_title,
                                                 "LOCK_SUBJ_PASSWORD",
                                                 "")
        self.disabled = True
        self.LOCK_IMG = LOCK_ON
    else:
        self.text = ""
        self.lock_password = ""
        self.disabled = False
        self.LOCK_IMG = LOCK_OFF

    # SETUP SCREEN!
    self.keep_looping = True

    # Experiment start
    with Loop(conditional=self.keep_looping):
        with Parallel():
            MouseCursor()
            recOut = Rectangle(width=s(INFO_WIDTH) + s(20),
                               height=s(INFO_HEIGHT) + s(20),
                               color=INFO_OUTLINE_COLOR)
            recin = Rectangle(width=s(INFO_WIDTH),
                              height=s(INFO_HEIGHT),
                              color=INFO_COLOR)
            lbl = Label(text=exp_title, center_x=recin.center_x,
                        top=recin.top - s(10),
                        font_size=s(INFO_FONT_SIZE))
            txtIn = TextInput(width=s(TEXT_INPUT_WIDTH),
                              height=s(TEXT_INPUT_HEIGHT),
                              font_size=s(INFO_FONT_SIZE),
                              center_x=recin.center_x,
                              top=lbl.bottom - s(20),
                              multiline=False, text=self.text,
                              disabled=self.disabled,
                              hint_text="Subject ID")
            with Loop():
                with ButtonPress():
                    Button(background_normal=self.LOCK_IMG,
                           left=txtIn.right, center_y=txtIn.center_y,
                           height=s(LOCK_HEIGHT),width=s(LOCK_WIDTH),
                           allow_stretch=True, keep_ratio=False)
                with If(self.LOCK_IMG == LOCK_ON):
                    with Parallel():
                        Rectangle(size=recin.size,
                                  center=recin.center,
                                  color=recin.color)
                        pwiOFF = TextInput(width=s(TEXT_INPUT_WIDTH),
                                        height=s(TEXT_INPUT_HEIGHT),
                                        font_size=s(INFO_FONT_SIZE),
                                        multiline=False,
                                        hint_text="Enter your lock password",
                                        center=recin.center)
                    with UntilDone():
                        with ButtonPress() as pwbpOFF:
                            Button(name="con", text="Continue",
                                   font_size=s(INFO_FONT_SIZE),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=pwiOFF.width/2., right=pwiOFF.right,
                                   background_color=INFO_OUTLINE_COLOR,
                                   top=pwiOFF.bottom - s(5))
                            Button(name="can", text="Cancel",
                                   font_size=s(INFO_FONT_SIZE),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=pwiOFF.width/2., left=pwiOFF.left,
                                   background_color=INFO_OUTLINE_COLOR,
                                   top=pwiOFF.bottom - s(5))
                    with If((pwiOFF.text == self.lock_password) & (pwbpOFF.pressed == "con")):
                        self.LOCK_IMG = LOCK_OFF
                        Func(KOConfig.set, exp_title, "LOCK_SUBJ_PASSWORD", "")
                        Func(KOConfig.write)
                        UpdateWidget(txtIn, disabled=False)
                    with Else():
                        Label(text="WRONG PASSWORD", duration=1.0,
                              font_size=s(INFO_FONT_SIZE),
                              color="RED")
                with Else():
                    with Parallel():
                        Rectangle(size=recin.size,
                                  center=recin.center,
                                  color=recin.color)
                        pwiON = TextInput(width=s(TEXT_INPUT_WIDTH),
                                        height=s(TEXT_INPUT_HEIGHT),
                                        font_size=s(INFO_FONT_SIZE),
                                        multiline=False,
                                        hint_text="Pick a lock password",
                                        center=recin.center)
                    with UntilDone():
                        with ButtonPress() as pwbpON:
                            Button(name="con", text="Continue",
                                   font_size=s(INFO_FONT_SIZE),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=pwiON.width/2., right=pwiON.right,
                                   background_color=INFO_OUTLINE_COLOR,
                                   top=pwiON.bottom - s(5))
                            Button(name="can", text="Cancel",
                                   font_size=s(INFO_FONT_SIZE),
                                   height=s(INFO_BUTTON_HEIGHT),
                                   width=pwiON.width/2., left=pwiON.left,
                                   background_color=INFO_OUTLINE_COLOR,
                                   top=pwiON.bottom - s(5))
                    with If(pwbpON.pressed == "con"):
                        with If((pwiON.text != "") & (pwiON.text != None)):
                            self.LOCK_IMG = LOCK_ON
                            Func(KOConfig.set, exp_title, "LOCK_SUBJ_PASSWORD", pwiON.text)
                            self.lock_password = pwiON.text
                            with If((txtIn.text == "") | (txtIn.text == None)):
                                self.text = "SUBJ000"
                                Func(KOConfig.set, exp_title, "LOCK_SUBJ", "SUBJ000")
                            with Else():
                                Func(KOConfig.set, exp_title, "LOCK_SUBJ", txtIn.text)
                            Func(KOConfig.write)
                            UpdateWidget(txtIn, disabled=True)

            bc = Button(text="Continue", font_size=s(INFO_FONT_SIZE),
                        height=s(INFO_BUTTON_HEIGHT),
                        width=s(INFO_BUTTON_WIDTH),
                        right=recin.right - s(20),
                        bottom=recin.bottom + s(20),
                        name="C",
                        background_normal="",
                        background_color=INFO_OUTLINE_COLOR)
            bconf = Button(text="Settings",
                           name="G",
                           height=s(INFO_BUTTON_HEIGHT),
                           width=s(INFO_BUTTON_WIDTH),
                           font_size=s(INFO_FONT_SIZE),
                           bottom=recin.bottom + s(20),
                           left=recin.left + s(20),
                           background_normal="",
                           background_color=INFO_OUTLINE_COLOR)
            Image(source=os.path.join(os.path.dirname(__file__),
                                            SMILE_IMG),
                  height=s(250), width=s(250),
                  keep_ratio=False, allow_stretch=True,
                  center_x=recin.center_x, opacity=.25,
                  center_y=recin.center_y - s(15))
        with UntilDone():
            bp = ButtonPress(buttons=[bc, bconf])
            Wait(.25)

        self.text = txtIn.text
        with If(bp.pressed == "C"):
            new_dir = Func(self.exp._change_smile_subj, Ref(str, txtIn.text))
            self.keep_looping = False

        with Elif(bp.pressed == "G"):
            mC = ConfigWindow()

if __name__ == "__main__":


    from experiment import Experiment

    exp = Experiment(background_color=(.35, .35, .35, 1.0),
                     Touch=False, debug=True)

    InputSubject()

    exp.run()
