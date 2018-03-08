




from state import State
from pylsl import StreamInfo, StreamOutlet

_lsl_outlet = None

def init_audio_server(server_name, server_type, nchans,
                      suggested_freq, dtype, unique_id="SMILE_LSL_OUT",):

    global _lsl_outlet

    #info = StreamInfo('MyMarkerStream3','Markers',1,0,'int32','bababooi513')
    info = StreamInfo(server_name, server_type, nchans, suggested_freq,
                     dtype, unique_id)
    _lsl_outlet = StreamOutlet(info)

class LSL_Pulse(CallbackState):

    def __init__(self, val, **kwargs):

        super(LSL_Pulse, self).__init__(parent=kwargs.pop("parent", None),
                                   repeat_interval=kwargs.pop("repeat_interval", None),
                                   duration=kwargs.pop("duration", 0.0),
                                   save_log=kwargs.pop("save_log", True),
                                   name=kwargs.pop("name", None),
                                   blocking=kwargs.pop("blocking", True))
        self._init_pulse_val = val


    def _callback(self):

        outlet.push_sample([self._pulse_val], clock.now())
        self._pulse_time = clock.now()
