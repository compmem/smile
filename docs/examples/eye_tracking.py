#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# load all the states
from smile.common import *
import tobii_research as tr
import TobiiPro_2
from TobiiPro_2 import TobiiProTracker
# from tobii_research_addons import ScreenBasedCalibrationValidation, Point2
from tba import ScreenBasedCalibrationValidation, Point2
# eye tracker
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import mm

# define calibration variables; these can be moved to a config file
sample_count = 200
timeout_ms = 1000
# targets for calibration
calibration_targets = [[(0.25, 0.5),
                       (0.75, 0.5)],
                       [(0.1, 0.1),
                       (0.9, 0.9)],
                       [(0.5, 0.1),
                       (0.1, 0.9)],
                       [(0.5, 0.9),
                       (0.9, 0.1)],
                       [(0.5, 0.5)]]
# targets for validation
targets = [(0.25, 0.5),
           (0.75, 0.5),
           (0.2, 0.2),
           (0.8, 0.8),
           (0.5, 0.2),
           (0.2, 0.8),
           (0.5, 0.8),
           (0.8, 0.2),
           (0.5, 0.5)]

points_to_collect = [Point2(x,y) for x,y in targets]
cal_keys = [str(i) for i in points_to_collect]
cal_dict = {}
for i in cal_keys:
    ind = cal_keys.index(i)
    cal_dict[i] = {'target': targets[ind],
                   'point': points_to_collect[ind]}
Debug(targets=targets)
Debug(pc=points_to_collect)
Debug(cal_dict=cal_dict)
print(targets)
print(points_to_collect)
print(cal_dict)
############################################################################


@Subroutine
def TobiiCalibration(self,track_box=True,
                     calibrate=True,
                     validation=True):
    """
    Tobii calibration
    """
    tt = TobiiPro_2.TobiiProTracker()
    Tobii = Ref.object(tt)
    screen_width = self._exp.screen.width
    screen_height = self._exp.screen.height
    screen_center_x = self._exp.screen.center_x
    screen_center_y = self._exp.screen.center_y
    self.targets = targets
    val_aoe = 0.05

    self.x0 = 0
    self.y0 = 0
    ############################################################################
    # Track Box
    # Give participant and experimentor(s) feedback participant's
    # position in the eyetracker's viewing area
    with If(track_box==True):
        with Parallel():
            SmallRectangle = Line(rectangle=((screen_width/2-(screen_width*.25)/2.),
                                             (screen_height/2-(screen_height*.25)/2.),
                                             screen_width*.25,
                                             screen_height*.25),
                                  color='blue',
                                  width=2)
            Distance = Label(text='Find a comfortable position within view \n \
                                   of the eyetracker. The box will turn green \n\
                                   when you are in a good position.',
                            halign='left',
                            center_x=screen_center_x,
                            center_y=screen_center_y,
                            font_size=40)


        # updating trackbox
        with UntilDone():
            Wait(1.0)
            # start_tracking
            Func(Tobii.start_tracking)
            # give eyetracker time to start
            Wait(1.5)
            with Parallel():
                Foc = Ellipse(color='red',
                              size=[screen_height*.1,screen_height*.1],
                              center_x=screen_center_x,
                              center_y=screen_center_y)
                BigRectangle = Rectangle(color=(1.,0.,0.,0.25),
                                         center_x=screen_center_x,
                                         center_y=screen_center_y,
                                         width=screen_width*(6./8),
                                         height=screen_height*(6./8))
            with UntilDone():
                with Loop():
                    self.gaze_sample = Tobii.sample
                    with If((self.gaze_sample['right_gaze_origin_validity']==1) &
                            (self.gaze_sample['left_gaze_origin_validity']==1)):
                        # calculating average distance from each eye to the screen
                        left_distance = self.gaze_sample['left_gaze_origin_in_trackbox_coordinate_system'][2]
                        right_distance = self.gaze_sample['right_gaze_origin_in_trackbox_coordinate_system'][2]
                        self.avg_distance = (right_distance+left_distance)/2.

                        with If((self.avg_distance > .25) & (self.avg_distance < .75)):
                            UpdateWidget(BigRectangle, width=screen_width*self.avg_distance*.75,
                                                height=screen_height*self.avg_distance*.75)
                            Debug(a=self.avg_distance, b=BigRectangle.disappeared, c=BigRectangle.color,
                                  height=BigRectangle.height, on_screen=BigRectangle.on_screen)

                        Debug(a="ONE")
                        self.left_status = 0.25 < left_distance < 0.85
                        self.right_status = 0.25 < right_distance < 0.85
                        with If((self.left_status==True) & (self.right_status==True)):
                            UpdateWidget(BigRectangle, color=(0.,1.,0.,.25))
                        with Else():
                            UpdateWidget(BigRectangle, color=(1.,0.,1.,.25))

                        #Foc.update(color='green')
                    with Else():
                        Debug(a="EYBOI")
                        #Foc.update(color='red')

            with UntilDone():
                KeyPress()
        Func(Tobii.stop_tracking)
    ############################################################################
    # Calibration
    with If(calibrate==True):
        Label(text='Calibration: Press ENTER to begin.', width=600, font_size=40)
        with UntilDone():
            KeyPress('ENTER')
        Wait(1.0)

        # Enter Calibration Mode
        Func(Tobii.calibration_mode_on)
        Wait(1.5)
        #with Parallel():
        #    Point = Image(source='face-smile.png',
        #                  center_x=screen_center_x,
        #                  center_y=screen_center_y,
        #                  size=(30,30))
        #    # Label(text='Focus on the smiley faces as they appear.\n\
        #    #             Press ENTER to begin calibration.')
        #with UntilDone():
            # KeyPress('ENTER')
        with Loop(targets) as target:
            # Present calibration target
            #uw = UpdateWidget(Point,
            #                  center_x=screen_width*target.current[0],
            #                  center_y=screen_height-screen_height*target.current[1],
            #                  size=(30,30), color=(1,1,1,1),
            #                  rotate=0)
            dot = Image(source='face-smile.png',
                        center_x=screen_width*target.current[0],
                        center_y=screen_height-screen_height*target.current[1],
                        size=(30,30))
            with UntilDone():
                Wait(until=dot.appear_time)
                # Give participant time to focus on target
                dot.rotate_origin = dot.center
                #Wait(1.0)

                dot.slide(rotate=1000, duration=1.5)
                # Collect calibration gaze data

                cal = Func(Tobii.calibration_collect_data, target.current)

                rct = Rectangle(color=(1,1,1,0), duration=.000001)
                Wait(until=rct.disappear_time)
                #ResetClock(cal.leave_time)
                # with If(Tobii.calibration_stat != tr.CALIBRATION_STATUS_SUCCESS):
                #     #Debug(OBAMA='OBAMA')
                # make it explode
                #Wait(1.0)
                explode = dot.slide(duration=0.5,
                                    width=50, height=50,
                                    color=(0, 0, 0, 0))
                Wait(until=explode.finalize_time)

        # Compute and Apply calibration
        Func(Tobii.calibration_compute_apply)
        ResetClock()
        Wait(0.5)
            #Debug(calibration_result=Tobii.calibration_result.status)
        Func(Tobii.calibration_mode_off)
    with If((calibrate==True)&(validation==True)):
        Wait(2.0)
    ############################################################################
    # Validation
    with If(validation==True):
        Func(Tobii.validation_mode_on)
        Label(text='Calibration Validation: Press ENTER to begin.', width=600, font_size=40)
        with UntilDone():
            KeyPress('ENTER')
        Wait(1.0)

        Func(Tobii.start_tracking)
        # Enter Validation Mode
        Func(Tobii.validation_mode_on)
        Wait(2.5)
        print("Entered validation mode for eye tracker with serial number {0}.".format(Tobii.eyetracker.serial_number))

        Pic = Image(source='face-smile.png',
                      center_x=screen_center_x,
                      center_y=screen_center_y,
                      size=(30,30))
        # position list
        with UntilDone():
            # with Loop(targets) as target:
            with Loop(points_to_collect) as point:
            # with Loop(targets) as targ:
                target = self.targets[point.i]
                # target = targ.current
                Debug(p=point.current)
                Debug(target=target)
                uw = UpdateWidget(Pic,
                                  center_x=screen_width*target[0],
                                  center_y=screen_height - screen_height*target[1])
                # Give participant time to focus on target
                rotation = 0
                stop = False
                with Loop(conditional=(stop==False)):
                    sample = Tobii.sample
                    left = sample['left_gaze_point_on_display_area']
                    right = sample['right_gaze_point_on_display_area']
                    Debug(right=right)
                    with If((target[0]-val_aoe<=left[0]<=target[0]+val_aoe)&
                            (target[1]-val_aoe<=left[1]<=target[1]+val_aoe)):
                        with Parallel():
                            Pic.slide(rotate=360,duration=1.)
                            # Collect  validation gaze data
                            with Serial():
                                Wait(0.1)
                                Debug(inserail='yas')
                                Debug(YYAA=point.current)
                                Func(Tobii.validation_collect_data,point.current)
                                # Func(Tobii.validation_collect_data,t)
                                with Loop(conditional=(Tobii.validation.is_collecting_data==True)) as l:
                                    Wait(0.5)
                                    Debug(waiting='yes')
                                Debug(waiting='no')
                                stop = True
                    Wait(1.)

            # Label(text='Calculating...',width=600,font_size=40)
            # with UntilDone():
            Func(Tobii.validation_compute)
        Wait(2.)

        # Exit validation mode
        Func(Tobii.validation_mode_off)
        Func(Tobii.stop_tracking)
        Wait(2.)

        # retrieve validation data
        Func(Tobii.validation_outcome)
        validation_data = Tobii.validation_data
        timeouts = Tobii.timeouts

        # check to see if any validation points failed
        # with If(Ref(len(timeouts)) > 0):
        #     Debug(num_timeouts=Ref(len(timeouts))

        # Present points and gaze samples
        with Parallel() as par:
            with Serial():
                with Loop(targets) as target:
                    #Debug(target=target.current)
                    with par.insert():
                        # with Loop(target.i) as img_loop:
                        Image(source='face-smile.png',
                              center_x=screen_width*target.current[0],
                              center_y=screen_height - screen_height*target.current[1],
                              size=(60,60))
                with Loop(validation_data) as point:
                    # Debug(pt=point.current)
                    left_eye = point.current['left_eye_gaze_point']
                    left_val = point.current['left_validity']
                    right_eye = point.current['right_eye_gaze_point']
                    right_val = point.current['right_validity']
                    avg_x = point.current['avg_gaze_point_x']
                    avg_y = point.current['avg_gaze_point_y']
                    # Debug(avg_x=avg_x)
                    # Debug(le=left_eye)
                    with Loop(left_eye) as spot:
                        with If(left_val[spot.i] == True):
                            with par.insert():
                                Ellipse(color='blue',
                                        size=(10,10),
                                        center_x=screen_width*spot.current[0],
                                        center_y=screen_height-screen_height*spot.current[1])
                    with Loop(right_eye) as spot:
                        with If(right_val[spot.i] == True):
                            with par.insert():
                                Ellipse(color='green',
                                        size=(10,10),
                                        center_x=screen_width*spot.current[0],
                                        center_y=screen_height-screen_height*spot.current[1])
                    with par.insert():
                        Ellipse(color='white',
                                size=(20,20),
                                center_x=screen_width*avg_x,
                                center_y=screen_height-screen_height*avg_y)
        with UntilDone():
            KeyPress()
            Screenshot(filename='meta_exp.png')



    Label(text='Validation Successful: Press ENTER to end.', width=600, font_size=40)
    with UntilDone():
        KeyPress('ENTER')
