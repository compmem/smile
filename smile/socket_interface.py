#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from state import CallbackState
from clock import clock

import sys
import socket

_sockets = {}


def init_socket_outlet(uniq_ID, server, port):
    """Sets up a socket that allows for TCP messaging.

    A *SocketPush* state will use a pre-initialized Socket to send out a
    marker to the specific server and port. Once created, the socket will be
    added to a dictionary of sockets (_sockets) where the key is a string joined
    by an *_*. EX **markersocket_127.0.0.1_1234**.

    Parameters
    ----------
    unique_id : string
        Unique identifier for this socket. Used only to differenciate this
        socket from other sockets initialized with this function.
    server : string
        Host name. For a local TCP process, use the string "localhost"
    port : int
        A port number for the server.

    Returns a Socket that is to be used in conjunction with the *SocketPush*
    state. Will return None if the connection could not be established.
    """


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
            sys.stdout.write("[ERROR  ] [SOCKET      ] Unable to establish a " +
                                      "connection for the socket at server %s and the port %i\n" % (server, port))
            return None


class SocketPush(CallbackState):
    """Pushes a message to the provided socket.

    A state that uses a preinitialized Socket to send a message to a specific
    server and port.

    socket : socket
        Preinitialized socket class using *init_socket_outlet*
    msg : string
        A string message that is to be passed to the specific socket.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    send_time : Float
        The time in which the message has finished being sent to the server.
        This value is in seconds and based on experiment time. Experiment time
        is the number of seconds since the start of the experiment.
    msg : string
        The message sent to the server.
    server_name : string
        The server the message is being sent to.
    port : int
        The port the message is being sent to in the server.
    rtn : int
        Number of bytes sent by this SocketPush. Check this value to make sure
        your entire message was sent.

    """


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

        self._log_attrs.extend(['rtn', 'msg', 'send_time', "port", "server"])


    def _enter(self):
        if self._socket is not None:
            self._server = self._socket.getsockname()[0]
            self._port = self._socket.getsockname()[1]
        else:
            self._server = None
            self._port = None


    def _callback(self):
        if self._socket is not None:
            self._rtn = self._socket.send(self._msg)
            self._send_time = clock.now()


if __name__ == "__main__":

    from experiment import Experiment
    from state import Wait, Parallel, Loop
    from video import Label

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
