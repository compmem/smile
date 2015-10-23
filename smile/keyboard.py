#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import os.path

from state import CallbackState
from ref import val, NotAvailable
from clock import clock
from experiment import Experiment
from log import LogWriter, log2csv


def Key(name):
    exp = Experiment._last_instance()
    return exp._app.get_key_ref(name.upper())


class KeyState(CallbackState):
    def __init__(self, parent=None, duration=None, save_log=True, name=None,
                 blocking=True):
        super(KeyState, self).__init__(parent=parent, duration=duration,
                                       save_log=save_log, name=name,
                                       blocking=blocking)

    def on_key_down(self, keycode, text, modifiers, event_time):
        self.claim_exceptions()
        self._on_key_down(keycode, text, modifiers, event_time)

    def _on_key_down(self, keycode, text, modifiers, event_time):
        pass

    def on_key_up(self, keycode, event_time):
        self.claim_exceptions()
        self._on_key_up(keycode, event_time)

    def _on_key_up(self, keycode, event_time):
        pass

    def _callback(self):
        self._exp._app.add_callback("KEY_DOWN", self.on_key_down)
        self._exp._app.add_callback("KEY_UP", self.on_key_up)

    def _leave(self):
        self._exp._app.remove_callback("KEY_DOWN", self.on_key_down)
        self._exp._app.remove_callback("KEY_UP", self.on_key_up)
        super(KeyState, self)._leave()


class KeyPress(KeyState):
    def __init__(self, keys=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(KeyPress, self).__init__(parent=parent,
                                       duration=duration,
                                       save_log=save_log,
                                       name=name,
                                       blocking=blocking)

        self._init_keys = keys
        self._init_correct_resp = correct_resp
        self._init_base_time = base_time
        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None

        # append log vars
        self._log_attrs.extend(['keys', 'correct_resp', 'base_time',
                                'pressed', 'press_time',
                                'correct', 'rt'])

    def _enter(self):
        super(KeyPress, self)._enter()
        # reset defaults
        self._pressed = NotAvailable
        self._press_time = NotAvailable
        self._correct = NotAvailable
        self._rt = NotAvailable
        if self._base_time is None:
            self._base_time = self._start_time
        if self._keys is None:
            self._keys = []
        elif type(self._keys) not in (list, tuple):
            self._keys = [self._keys]
        if self._correct_resp is None:
            self._correct_resp = []
        elif type(self._correct_resp) not in (list, tuple):
            self._correct_resp = [self._correct_resp]

    def _on_key_down(self, keycode, text, modifiers, event_time):
        sym_str = keycode[1].upper()
        if not len(self._keys) or sym_str in self._keys:
            # it's all good!, so save it
            self._pressed = sym_str
            self._press_time = event_time
            
            # calc RT if something pressed
            self._rt = event_time['time'] - self._base_time

            self._correct = self._pressed in self._correct_resp

            # let's leave b/c we're all done
            self.cancel(event_time['time'])

    def _leave(self):
        super(KeyPress, self)._leave()
        if self._pressed is NotAvailable:
            self._pressed = ''
        if self._press_time is NotAvailable:
            self._press_time = None
        if self._correct is NotAvailable:
            self._correct = False
        if self._rt is NotAvailable:
            self._rt = None


class KeyRecord(KeyState):
    def __init__(self, parent=None, duration=None, name=None, blocking=True):
        super(KeyState, self).__init__(parent=parent, duration=duration,
                                       save_log=False, name=name,
                                       blocking=blocking)

    def begin_log(self):
        super(KeyRecord, self).begin_log()
        title = "keyrec_%s_%d_%s" % (
            os.path.splitext(
                os.path.basename(self._instantiation_filename))[0],
            self._instantiation_lineno,
            self._name)
        self.__log_filename = self._exp.reserve_data_filename(title, "slog")
        self.__log_writer = LogWriter(self.__log_filename,
                                      ["timestamp", "key", "state"])

    def end_log(self, to_csv=False):
        super(KeyRecord, self).end_log(to_csv)
        if self.__log_writer is not None:
            self.__log_writer.close()
            self.__log_writer = None
            if to_csv:
                csv_filename = (os.path.splitext(self.__log_filename)[0] +
                                ".csv")
                log2csv(self.__log_filename, csv_filename)

    def _on_key_down(self, keycode, text, modifiers, event_time):
        self.__log_writer.write_record({
            "timestamp": event_time,
            "key": keycode[1].upper(),
            "state": "down"})

    def _on_key_up(self, keycode, event_time):
        self.__log_writer.write_record({
            "timestamp": event_time,
            "key": keycode[1].upper(),
            "state": "up"})


if __name__ == '__main__':

    from experiment import Experiment
    from state import Wait, Debug, Loop, UntilDone, Log, Meanwhile

    exp = Experiment()
    with Meanwhile():
        KeyRecord(name="record_all_key_presses")

    Debug(name='Press T+G+D or SHIFT+Q+R')
    Wait(until=((Key("T") & Key("G") & Key("D")) |
                (Key("SHIFT") & Key("Q") & Key("R"))))
    Debug(name='Key Press Test')

    exp.last_pressed = ''
    with Loop(conditional=(exp.last_pressed!='K')):
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        exp.last_pressed = kp.pressed
        Log(pressed=kp.pressed, rt=kp.rt)

    KeyRecord()
    with UntilDone():
        kp = KeyPress(keys=['J','K'], correct_resp='K')
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

        kp = KeyPress()
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

        kp = KeyPress(duration=2.0)
        Debug(pressed=kp.pressed, rt=kp.rt, correct=kp.correct)
        Wait(1.0)

    exp.run()
    
