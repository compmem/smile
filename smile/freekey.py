#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


from .keyboard import KeyPress
from .state import Loop, If, Elif, Else, Subroutine
from .state import UntilDone, Wait, ResetClock
from .ref import Ref
from .clock import clock
from .video import Label

# set the allowable keys (A-Z)
#@FIX: unichr -> chr
asciiplus = [str(chr(i)) for i in range(65,65+26)]
asciiplus += ['ENTER','BACKSPACE','SPACEBAR']
asciiplus += ['%d'%i for i in range(10)]

@Subroutine
def FreeKey(self, lbl, max_duration=10.0, max_resp=100, base_time=None):
    """
    Perform free recall typed responses.

    Parameters
    ----------
    lbl : Label state
        The text that will appear on the screen to indicate to the
        participant that they are to type a response. This text
        will disappear from the screen when a response is
        begun and return when ready for the next response. It's a
        good idea to use something like a label with '???????'.
    max_duration : {10.0, float}
        The amount of time in seconds that the participant is given
        to respond.
    max_resp : {100, int}
        Maximum number of responses that the participant is allowed
        to enter.
    base_time : float
        Manually set a time reference for the start of the state. This
        will be used to calculate reaction times.

    Example
    --------
    FreeKey(Label('???????'), max_duration=15.0)
    The message '??????' will appear on the screen,
    and participants will be given 15 seconds to enter a response,
    replacing that text. They can enter as many responses as possible
    in the 15 second time period.

    Log Parameters
    ---------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for additional logged parameters.

    responses : list
        List of typed responses, each with the following information:
        first_key_time, first_key_rt, enter_key_time, enter_key_rt,
        response, response_num.
        The time is the actual time, the rt is the time since the
        base_time.
    """
    # I'd like the lbl to be up until the below is done. How?
    # is it just that I would cancel it at the end here?
    #lbl = Label(text=txt, font_size=40)
    self.claim_child(lbl)
    with UntilDone():

        # container for responses
        self.responses = []

        # info for each response
        self.fk_num_resp = 0
        self.fk_first_key_time = 0
        self.fk_first_key_rt = 0
        self.fk_cur_resp = ''

        # save the starting text and base time
        self.fk_start_text = lbl.text

        # handle starting values
        self.max_duration = max_duration
        self.max_resp = max_resp

        # handle the base time
        with If(base_time):
            # use the passed value
            self.base_time = base_time
        with Else():
            # make sure it's available
            #Debug(fk_on_screen=lbl.on_screen)
            Wait(until=lbl.on_screen)
            #Debug(fk_on_screen=lbl.on_screen)

            # use the label's appear time
            self.base_time = lbl.appear_time['time']

        # reset timing to the desired base_time
        ResetClock(self.base_time)

        # collect responses for the desired max_duration or max_resp
        with Loop():
            # accept a key response, time is based on label's ontime
            kp = KeyPress(keys=asciiplus, base_time=self.base_time)

            # process the key
            with If(kp.pressed == 'BACKSPACE'):
                # if there is text, remove a char
                with If(self.fk_cur_resp != ''):
                    self.fk_cur_resp = self.fk_cur_resp[:-1]
                    lbl.text = self.fk_cur_resp
            with Elif(kp.pressed == 'ENTER'):
                # if there is text, log as a response
                # increment the response counter
                self.fk_num_resp += 1

                # append the response to the list
                self.responses += [Ref(dict,
                                       response=self.fk_cur_resp,
                                       response_num=self.fk_num_resp,
                                       first_key_time=self.fk_first_key_time,
                                       first_key_rt=self.fk_first_key_rt,
                                       enter_key_time=kp.press_time,
                                       enter_key_rt=kp.rt)]

                # set starting text back and reset text
                self.fk_cur_resp = ''
                with If(self.fk_num_resp < self.max_resp):
                    # gonna keep going
                    lbl.text = self.fk_start_text
            with Else():
                # new key, so append it
                # if it's first key, save the time
                with If(self.fk_cur_resp == ''):
                    self.fk_first_key_rt = kp.rt
                    self.fk_first_key_time = kp.press_time

                # append the text
                with If(kp.pressed == 'SPACEBAR'):
                    # handle the space
                    self.fk_cur_resp += ' '
                with Else():
                    # just append the letter
                    self.fk_cur_resp += kp.pressed

                # update the label
                lbl.text = self.fk_cur_resp

        with UntilDone():
            Wait(max_duration, until=(self.fk_num_resp >= max_resp))

        # ran out of time, see if there is an unfinished response
        with If(self.fk_cur_resp != ''):
            # there is something, so log it, too
            # increment the response counter
            self.fk_num_resp += 1

            # append the response to the list, but with no Enter key time
            self.responses += [Ref(dict,
                                   response=self.fk_cur_resp,
                                   response_num=self.fk_num_resp,
                                   first_key_time=self.fk_first_key_time,
                                   first_key_rt=self.fk_first_key_rt,
                                   enter_key_time=None,
                                   enter_key_rt=None)]


if __name__ == '__main__':

    from .experiment import Experiment
    from .state import Wait, Debug
    from .video import Label

    exp = Experiment()

    Wait(.5)

    fk = FreeKey(Label(text='XXXXXX',font_size=40), max_resp=1)
    Debug(responses=fk.responses)

    Label(text='Done', font_size=32, duration=2.0)

    fk2 = FreeKey(Label(text='??????',font_size=30))
    Debug(responses=fk2.responses)

    Wait(1.0)

    exp.run()
