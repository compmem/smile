from state import Subroutine, Parallel, Serial, Loop, If, Else, Elif, \
                  UntilDone, ResetClock, Func
from video import Rectangle, ProgressBar, Label, UpdateWidget, \
                  CheckBox, TextInput, ButtonPress, Button, Image
from ref import Ref
from mouse import MouseCursor
from scale import scale as s
from kivy_overrides import Config as KOConfig
import kivy_overrides as KO

import os

@Subroutine
def FrameTest(self,
              INFO_WIDTH=500,
              INFO_HEIGHT=600,
              INFO_OUTLINE_COLOR=[51./255., 107./255., 135./255.],
              INFO_COLOR=[144./255., 175./255., 197./255.],
              INFO_FONT_SIZE=30,
              num_flips=500,
              to_skip=5,
              ):

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
                          color=[144./255.,175./255.,197./255.],
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


@Subroutine
def ConfigWindow(self,
                 params,
                 INFO_WIDTH=500,
                 INFO_HEIGHT=600,
                 INFO_OUTLINE_COLOR=[51./255., 107./255., 135./255.],
                 INFO_COLOR=[144./255., 175./255., 197./255.],
                 INFO_BUTTON_WIDTH=200,
                 INFO_BUTTON_HEIGHT=50,
                 INTRO_WIDTH=700,
                 INTRO_HEIGHT=500,
                 TEXT_INPUT_WIDTH=300,
                 TEXT_INPUT_HEIGHT=50,
                 INFO_FONT_SIZE=30,
                 CHECK_HEIGHT=25,
                 CHECK_WIDTH=25,
                 CONT_KEY=["SPACEBAR"],
                 TOUCH=False):

    self.params = params
    self.canceled = True
    self.keep_looping = True
    self.lock_state = Ref.cond(self.params["locked"], "down", "normal")
    self.frameText = Ref(str, self.params['frame_rate'])

    with Loop(conditional=self.keep_looping):
        with Parallel():
            with If(self.exp._platform != "android"):
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

            # SUBJECT ID LOCK

            lRec = Rectangle(color="GRAY",
                             left=recin.left + s(20),
                             top=title.bottom - s(40),
                             height=s(CHECK_HEIGHT),
                             width=s(CHECK_WIDTH))
            cb_l = CheckBox(name="tog_lock", state=self.lock_state,
                            center_y=lRec.center_y,
                            center_x=lRec.center_x,
                            height=s(CHECK_HEIGHT),
                            width=s(CHECK_WIDTH),
                            allow_stretch=True, keep_ratio=False)
            lbl_lock = Label(text="Lock the Subject ID",
                             center_y=lRec.center_y,
                             left=lRec.right + s(50),
                             font_size=s(INFO_FONT_SIZE))

            timeInput = TextInput(text=self.frameText,
                                  font_size=s(INFO_FONT_SIZE),
                                  width=s(TEXT_INPUT_WIDTH)/3.,
                                  height=s(TEXT_INPUT_HEIGHT),
                                  left=recin.left + s(20),
                                  top=lRec.bottom - s(40),
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
            timeLabel = Label(text="Density: "%(),
                              top=timeInput.bottom - s(40),
                              left=recin.left + s(20),
                              font_size=s(INFO_FONT_SIZE))


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
                                      timing_button])

        with If(bp.pressed == "apply"):
            self.locked = Ref.cond(cb_l.state == "down", 1, 0)
            self.exp.flip_interval = 1./Ref(float, timeInput.text)
            self.framerate = Ref(float, timeInput.text)
            self.canceled = False
            self.keep_looping = False
        with Elif(bp.pressed == "timing"):
            ft = FrameTest()
            self.frameText = ft.framerate
        with Else():
            self.keep_looping = False

@Subroutine
def SubjectInput(self,
                 SHOW_SPLASH=True,
                 INFO_WIDTH=500,
                 INFO_HEIGHT=600,
                 INFO_OUTLINE_COLOR=[51./255., 107./255., 135./255.],
                 INFO_COLOR=[144./255., 175./255., 197./255.],
                 INFO_BUTTON_WIDTH=200,
                 INFO_BUTTON_HEIGHT=50,
                 INTRO_WIDTH=700,
                 INTRO_HEIGHT=500,
                 TEXT_INPUT_WIDTH=300,
                 TEXT_INPUT_HEIGHT=50,
                 INFO_FONT_SIZE=30,
                 CONT_KEY=["SPACEBAR"],
                 TOUCH=False):
                 
    if SHOW_SPLASH:



    if KOConfig.getdefaultint("SMILE", "LOCKEDSUBJID", 0):
        self.text=KOConfig.getdefault("SMILE", "SUBJID", "subj000")
        self.disabled = True
    else:
        self.text = ""
        self.disabled = False

    # SETUP SCREEN!
    self.keep_looping = True

    # Experiment start
    with Loop(conditional=self.keep_looping):
        with Parallel():
            if not TOUCH:
                MouseCursor()
            recOut = Rectangle(width=s(INFO_WIDTH) + s(20),
                               height=s(INFO_HEIGHT) + s(20),
                               color=INFO_OUTLINE_COLOR)
            recin = Rectangle(width=s(INFO_WIDTH),
                               height=s(INFO_HEIGHT),
                              color=INFO_COLOR)
            lbl = Label(text="Cognitive Battery", center_x=recin.center_x,
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
            Image(source=os.path.join("assets","face-smile.png"),
                  height=s(250), width=s(250),
                  keep_ratio=False, allow_stretch=True,
                  center_x=recin.center_x, opacity=.25,
                  center_y=recin.center_y - s(15))
        with UntilDone():
            bp = ButtonPress(buttons=[bc, bconf])
        self.text = txtIn.text
        with If(bp.pressed == "C"):
            new_dir = Func(self.exp._change_smile_subj, Ref(str, txtIn.text))
            self.keep_looping = False

        with Elif(bp.pressed == "G"):
            resy = Func(KO._get_config)
            mC = ConfigWindow(resy.result, )
            with If(mC.canceled == False):
                Func(KO._set_config, locked=mC.locked, framerate=mC.framerate)
                with If(mC.locked):
                    self.disabled = True
                    with If((txtIn.text == "") | (txtIn.text == None)):
                        self.text = "SUBJ000"
                        Func(KOConfig.set, "SMILE", "SUBJID", "SUBJ000")
                    with Else():
                        Func(KOConfig.set, "SMILE", "SUBJID", txtIn.text)
                    Func(KOConfig.write)
                with Else():
                    self.disabled = False

if __name__ == "__main__":


    from experiment import Experiment

    exp = Experiment(background_color=(.35, .35, .35, 1.0))

    SubjectInput(TOUCH=False)

    exp.run()
