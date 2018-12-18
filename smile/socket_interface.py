#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import CallbackState, Wait, Parallel, Loop
from video import Label
from clock import clock

import socket

_sockets = {}


def init_socket_outlet(uniq_ID, server, port):

    global _sockets

    unique_identifier = "_".join([uniq_ID, server, str(port)])

    if unique_identifier in _sockets.keys():
        return _sockets[unique_identifier]

    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            rtn = sock.connect((server, port))
            _sockets[unique_identifier] = sock
            return _sockets[unique_identifier]

        except:
            sys.stdout.write("[ERROR  ] [SOCKET      ] Unable to establish a Connection. TCP pulses disabled for this Socket")
            return None


class SocketPush(CallbackState):

    def __init__(self, socket, msg,  **kwargs):

        super(SocketPush, self).__init__(parent=kwargs.pop("parent", None),
                                         repeat_interval=kwargs.pop("repeat_interval", None),
                                         duration=kwargs.pop("duration", 0.0),
                                         save_log=kwargs.pop("save_log", True),
                                         name=kwargs.pop("name", None),
                                         blocking=kwargs.pop("blocking", True))
        self._init_socket = socket
        self._init_msg = msg
        self._rtn = None
        self._send_time = None

        self._log_attrs.extend(['rtn', 'msg', 'send_time'])

    def _callback(self):

        if self._socket is not None:
            self._rtn = self._socket.send(self._msg)
            self._send_time = clock.now()


if __name__ == "__main__":

    from experiment import Experiment

    # Initialize the outlet
    OUTLET = init_socket_outlet(uniq_ID='SocketMarket', server='localhost',
                                port=1234)

    exp = Experiment()

    # Signal the beginning of the experiment.
    SocketPush(socket=OUTLET, msg="<TRIGGER>300</TRIGGER>")

    # Wait for the experiment to start!
    Wait(2.)

    with Parallel():

        Label(text="We will now push 10 markers.", blocking=False)
        with Loop(10, blocking=False):

            # Create the push state
            push_out = SocketPush(socket=OUTLET, msg="<TRIGGER>55</TRIGGER>")

            # Log send_time if you want easy access
            #Log(name="MARKERS",
            #    push_time=push_out.send_time)

            Wait(1.)

    exp.run()
