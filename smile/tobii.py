# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from smile.clock import *
from smile.clock import Clock
from smile.log import LogWriter
import tobii_research as tr

#import tobii_research_addons
# from tba import vectormath, ScreenBasedCalibrationValidation
from tobii_research_addons import *
import ctypes, os
import time
import numpy as np
import pickle
class TobiiProTracker():

    """

    Helper class for calibrating and recording TobiiPro data.

    """
    def __init__(self, tracker_id=None):
        """
        """

        # initialize the gaze data list
        self.gaze = []
        self.sample = None
        # not writing to file, yet
        self._log_file = None

        # not yet tracking
        self.tracking = False

        # not yet calibrated
        self.calibration_result = None

        # pick a tracker
        if tracker_id:
            # search for that eyetracker only
            self.eyetrackers = [t for t in tr.find_all_eyetrackers()
                                if t.serial_number == tracker_id]
        else:
            # get a list of all trackers (we'll pick the first)
            self.eyetrackers = tr.find_all_eyetrackers()
        # pick the first if we have one
        if self.eyetrackers:
            self.eyetracker = self.eyetrackers[0]
        else:
            # raise a warning
            print('WARNING! No matching eyetracker found!')
            self.eyetracker = None

    def _on_gaze_data(self, gaze_data):
        # add times for sync
        gaze_data.update({'smile_time': clock.now(),
                          'tracker_time': tr.get_system_time_stamp()})

        # append data to stream
        self.gaze.append(gaze_data)
        self.sample = gaze_data
        # write to file if writing
        if self._log_file:
            self._log_file.write_record(gaze_data)

    def start_tracking(self):
        # can only record if there is an eytracker
        if self.tracking:
            print('WARNING! Already tracking with eyetracker.')
            self.gaze = []
        else:
            self.gaze = []
            # subscribe to the eyetracker stream
            self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA,
                                         self._on_gaze_data,
                                         as_dictionary=True)
            time.sleep(1) # not sure why they want this
            self.tracking = True

    def stop_tracking(self):
        if self.tracking:
            # unsubscribe from the stream
            self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA)
            self.tracking = False

            # close the file if recording
            self.stop_recording()
        else:
            print('WARNING! Not already recording.')

    def start_recording(self, filename):
        # set the logfile
        self._log_file = LogWriter(filename)

        # start tracking if not already (will reset gaze)
        self.start_tracking()

    def stop_recording(self):
        if self._log_file:
            # close it (flushing data)
            self._log_file.close()

            # set it to none to stop trying to write
            self._log_file = None
    ############################################################################
    # Calibration Code
    def calibration_mode_on(self):
        self.calibration = tr.ScreenBasedCalibration(self.eyetracker)
        self.calibration.enter_calibration_mode()

    def calibration_collect_data(self,point):
        self.calibration.collect_data(point[0],point[1])

    def calibration_compute_apply(self):
        self.calibration_result = self.calibration.compute_and_apply()

    def calibration_mode_off(self):
        self.calibration.leave_calibration_mode()
    def calibration_save(self,filename='saved_calibration.bin'):
        # Save the calibration to file.
        with open(filename, "wb") as f:
            calibration_data = self.eyetracker.retrieve_calibration_data()
            # None is returned on empty calibration.
            if calibration_data is not None:
                print("Saving calibration to file for eye tracker with serial number {0}.".format(self.eyetracker.serial_number))
                f.write(self.eyetracker.retrieve_calibration_data())
            else:
                print("No calibration available for eye tracker with serial number {0}.".format(self.eyetracker.serial_number))
    ############################################################################
    # Validation Code

    def validation_outcome(self):
        # Store validation data, both overal and for each validation point

        # output list
        self.validation_data = []
        self.timeouts = []
        # Get gaze data for each calibration point
        keys = list(self.validation_result.points.keys())

        for key in keys:
            x = {'point':key,
                 'left_eye_gaze_point':[],
                 'right_eye_gaze_point':[],
                 'left_validity':[],
                 'right_validity':[],
                 'left_eye_origin_trackbox': [],
                 'right_eye_origin_trackbox': [],
                 'left_pupil_diameter': [],
                 'right_pupil_diameter': [],
                 }
            cal_pt = self.validation_result.points[key][0]
            # check for timeout
            if cal_pt.timed_out == True:
                self.timeouts.append(key)

            # get point averages
            x['avg_accuracy_left'] = cal_pt.accuracy_left_eye
            x['avg_accuracy_right'] = cal_pt.accuracy_right_eye
            x['avg_precision_left'] = cal_pt.precision_left_eye
            x['avg_precision_right'] = cal_pt.precision_right_eye
            x['avg_precision_rms_left'] = cal_pt.precision_rms_left_eye
            x['avg_precision_rms_right'] = cal_pt.precision_rms_right_eye

            # get gaze samples
            for sample in cal_pt.gaze_data:
                x['left_eye_gaze_point'].append(sample.left_eye.gaze_point.position_on_display_area)
                x['right_eye_gaze_point'].append(sample.right_eye.gaze_point.position_on_display_area)
                x['left_validity'].append(sample.left_eye.gaze_point.validity)
                x['right_validity'].append(sample.right_eye.gaze_point.validity)
                x['left_eye_origin_trackbox'].append(sample.left_eye.gaze_origin.position_in_track_box_coordinates)
                x['right_eye_origin_trackbox'].append(sample.right_eye.gaze_origin.position_in_track_box_coordinates)
                x['left_pupil_diameter'].append(sample.left_eye.pupil.diameter)
                x['right_pupil_diameter'].append(sample.right_eye.pupil.diameter)

            # get gaze point average; used in determining if gaze is near
            # validation point
            xs = []
            ys = []
            for i in range(len(x['left_eye_gaze_point'])):
                x1 = x['left_eye_gaze_point'][i][0]
                x2 = x['right_eye_gaze_point'][i][0]
                y1 = x['left_eye_gaze_point'][i][1]
                y2 = x['right_eye_gaze_point'][i][1]
                xs.append(x1)
                xs.append(x2)
                ys.append(y1)
                ys.append(y2)
            x['avg_gaze_point_x'] = float(np.average(xs))
            x['avg_gaze_point_y'] = float(np.average(ys))
            print(x['avg_gaze_point_x'])
            self.validation_data.append(x)
        pickle.dump(self.validation_data,open('validation_data.p','wb'))

    def validation_mode_on(self):
        # Turn on Validation Mode
        # using these values for now; will put these arguments in config file
        sample_count = 200
        timeout_ms = 1000

        self.validation = ScreenBasedCalibrationValidation(self.eyetracker,
                                                            sample_count,
                                                            timeout_ms)
        self.validation.enter_validation_mode()

    def validation_collect_data(self,point):
        # Collects data in relation to the given target validation point
        self.validation.start_collecting_data(point)

    def validation_compute(self):
        # performs validation calculations that are in the Tobii Pro SDK addon
        self.validation_result = self.validation.compute()

    def validation_mode_off(self):
        # Deactivate validation mode
        self.validation.leave_validation_mode()
