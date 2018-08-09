#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .state import CallbackState, Wait, Parallel, Loop
from .video import Label
from .clock import clock
from .pylsl import StreamInfo, StreamOutlet

_lsl_outlets = {}

def init_lsl_outlet(server_name, server_type, nchans,
                    suggested_freq, channel_format, unique_id="SMILE_LSL_OUT",):
    """Sends a Marker to a specified LSL.

    A *LSLPush* state will use a pre-initialized LSL outlet to send out a
    marker to the Lab Streaming Layer.

    Parameters
    ----------
    server_name : string
        Name of the stream. Describes the device (or product series) that this
        stream makes available (for use by programs, experimenters or data
        analysts).
    server_type : string
        Content type of the stream. By convention LSL uses the content types
        defined in the XDF file format specification where applicable
        (https://github.com/sccn/xdf). The content type is the preferred way to
        find streams (as opposed to searching by name). This should be set to
        "Markers" when sending sync triggers.
    nchans : integer
        Number of channels per sample. This stays constant for the lifetime of
        the stream. This number should be 1 for sending a sync marker.
    suggested_freq : integer
        The sampling rate (in Hz) as advertised by the data source, regular
        (otherwise set to IRREGULAR_RATE).
    channel_format : string
        Format/type of each channel. If your channels have different formats,
        consider supplying multiple streams or use the largest type that can
        hold them all (such as cf_double64). It is also allowed to pass this as
        a string, without the cf_ prefix, e.g., 'float32'
    unique_id : string (defaut = "SMILE_LSL_OUT", optional)
        Unique identifier of the device or source of the data, if available
        (such as the serial number). This is critical for system robustness
        since it allows recipients to recover from failure even after the
        serving app, device or computer crashes (just by finding a stream with
        the same source id on the network again). Therefore, it is highly
        recommended to always try to provide whatever information can uniquely
        identify the data source itself.

    Returns a StreamOutlet class that is to be used in conjunction with the
    *LSLPush* state.

    """
    global _lsl_outlets

    s = "_"
    unique_identifier = s.join([server_name, server_type, str(nchans),
                                str(suggested_freq), str(channel_format),
                                str(unique_id)])

    if unique_identifier in _lsl_outlets.keys():
        return _lsl_outlets[unique_identifier]
    else:
        info = StreamInfo(server_name, server_type, nchans, suggested_freq,
                          channel_format, unique_id)
        _lsl_outlets[unique_identifier] = StreamOutlet(info)
        return _lsl_outlets[unique_identifier]



class LSLPush(CallbackState):
    """Sends a Marker to a specified LSL.

    A *LSLPush* state will use a pre-initialized LSL outlet to send out a
    marker to the Lab Streaming Layer.

    Parameters
    ----------
    server : StreamOutlet
        The server that you would like to push data out to. This can easily be
        setup by running the *init_lsl_outlet* function defined in **lsl.py**.
    val : object
        The value of the marker you would like to send to the LSL. Can either
        be an object or a list of objects, depending on the nchans defined for
        the server.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    push_time : Float
        The time in which the pulse has finished sending to the LSL. This value
        is in seconds and based on experiment time. Experiment time is the
        number of seconds since the start of the experiment.

    NOTE
    ---------------------
    It is highly recommended to send a TEST PULSE at the beginning of your
    experiment. Some systems use the first pulse as a signal to start listening
    to a particular server closely, so you need to send a pulse at the start of
    your experiment in order to *wake up* the LSL listener.

    """


    def __init__(self, server, val, **kwargs):

        super(LSLPush, self).__init__(parent=kwargs.pop("parent", None),
                                      repeat_interval=kwargs.pop("repeat_interval", None),
                                      duration=kwargs.pop("duration", 0.0),
                                      save_log=kwargs.pop("save_log", True),
                                      name=kwargs.pop("name", None),
                                      blocking=kwargs.pop("blocking", True))
        self._init_server = server
        self._init_push_val = val
        self._push_time = None

        self._log_attrs.extend(['push_val', 'push_time'])


    def _callback(self):
        if type(self._push_val) != list:
            self._server.push_sample([self._push_val])
        else:
            self._server.push_sample(self._push_val)
        self._push_time = clock.now()



if __name__ == "__main__":

    from .experiment import Experiment

    exp = Experiment()

    # Initialize the outlet
    OUTLET = init_lsl_outlet(server_name='MarkerStream',
                             server_type='Markers',
                             nchans=1,
                             suggested_freq=500,
                             channel_format='int32',
                             unique_id='SMILE_LSL_OUT')

    # Signal the beginning of the experiment.
    LSLPush(server=OUTLET,
            val=55)

    # Wait for the experiment to start!
    Wait(2.)

    with Parallel():

        Label(text="We will now push 10 markers.", blocking=False)
        with Loop(10, blocking=False):

            # Create the push state
            push_out = LSLPush(server=OUTLET,
                               val=111)

            # Log like this if you want.
            #Log(name="MAKERS",
            #    push_time=push_out.push_time)

            Wait(1.)

    exp.run()
