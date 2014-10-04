#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


from keyboard import KeyPress,key
from video import Text,Unshow,Update
from state import Serial, Loop, Wait, If, now, Ref, val
from experiment import Log, Set, Get

import string

# set the allowable keys (A-Z)
asciiplus = [str(unichr(i)) for i in range(65,65+26)]
asciiplus += ['RETURN','ENTER','BACKSPACE','SPACE']
asciiplus += ['_%d'%i for i in range(10)]

class FreeKey(Serial):
    """
    Perform free recall typed responses.
    
    Parameters
    ----------
    txt : str
        The text that will appear on the screen to indicate to the
        participant that they are to type a response. This text
        will disappear from the screen when a response is
        entered. Default is '??????'.
    max_duration : {0.0, float}
        The amount of time in seconds that the participant is given
        to respond.
    max_resp : {100, int}
        Maximum number of characters that the participant is allowed
        to enter.
    base_time : int
        Manually set a time reference for the start of the state. This
        will be used to calculate reaction times.
    duration : {0.0, float}
        Duration of the state in seconds.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    save_log : bool
        If set to 'True,' details about the state will be
        automatically saved in the log files.      
        
    Example
    --------
    FreeKey('Please type a response.', max_duration=15.0)
    The message 'Please type a response.' will appear on the screen,
    and participants will be given 15 seconds to enter a response.
    
    Log Parameters
    ---------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters. 
        fk_start_text : 
            See 'txt parameter.
        fk_first_time : 
            Time of participant's initial key press.
        fk_end_time : 
            Total time participant was given to respond.
        fk_cur_text : 
            What the participant has typed at the time of the last flip.
        fk_num_resp :
            How many characters the participant has typed at the time
            of the last flip.
        fk_responses
            Complete response.
        keys
            Possible response keys.
        pressed
            Record of each key pressed within the alotted time.
        rt
            Amount of time that has passed for each key pressed,
            using base_time as a reference.      
    """
    def __init__(self, txt=None, max_duration=10.0, max_resp=100, base_time=None, 
                 duration=-1, parent=None, save_log=True):
        super(FreeKey, self).__init__(parent=parent, duration=duration, 
                                      save_log=save_log)

        # show the initial text
        if txt is None:
            txt = Text('??????', parent=self)
        else:
            # claim that text
            self.claim_child(txt)

        # set config vars
        self.max_resp = max_resp
        self.max_duration = max_duration
        self.responses = []

        # set self as parent
        # like using with, but without the indentation
        self.__enter__()

        # save the starting text
        Set('fk_start_text',txt['shown'].text)

        # set base_time
        if base_time is None:
            base_time = txt['first_flip']['time']

        # Loop until out of time or press enter
        Set('fk_first_time',0)
        Set('fk_end_time', base_time+max_duration)
        Set('fk_cur_text','')
        Set('fk_num_resp', 0)
        Set('fk_responses', [])
        cond = ((Get('fk_end_time')>Ref(gfunc=now)) &
                (Get('fk_num_resp')<Ref(self).max_resp))
        with Loop(conditional=cond) as loop:
            # accept keyboard response (for remaining duration)
            kp = KeyPress(keys=asciiplus, base_time=base_time,
                          until=Get('fk_end_time')<Ref(gfunc=now))

            # process the key
            # if Backspace remove the end
            if_backspace = If((kp['pressed'] == 'BACKSPACE'))
            with if_backspace.true_state:
               # if there's text
               with If(Get('fk_cur_text')!='').true_state:
                   # delete last char
                   Set('fk_cur_text',Get('fk_cur_text')[:-1])

                   # update the text
                   Update(txt, 'text', Get('fk_cur_text'))

            with if_backspace.false_state:
                # see if Enter
                if_enter = If((kp['pressed'] == 'ENTER')|(kp['pressed']=='RETURN'))
                with if_enter.true_state:
                    # is Enter, so log
                    Set('fk_num_resp', Get('fk_num_resp')+1)
                    resp = Ref(dict)(first_key_time=Get('fk_first_time'),
                                     enter_key_time=kp['press_time'],
                                     response=Get('fk_cur_text'),
                                     response_num=Get('fk_num_resp'))
                    Set('fk_responses', Get('fk_responses').append(resp))
                    # Log(first_key_time=Get('fk_first_time'),
                    #     enter_key_time=kp['press_time'],
                    #     response=Get('fk_cur_text'),
                    #     response_num=Get('fk_num_resp'))

                    # start over
                    Set('fk_cur_text','')
                    Update(txt, 'text', Get('fk_start_text'))

                with if_enter.false_state:
                    # is a new letter, so process it
                    # if first letter, then save the time
                    If(Get('fk_cur_text')=='',
                       Set('fk_first_time',kp['press_time']))

                    # else normal letter, append it (processing SPACE)
                    If(kp['pressed']=='SPACE',
                       Set('fk_cur_text', Get('fk_cur_text')+' '),
                       Set('fk_cur_text', Get('fk_cur_text')+
                           Ref(string.strip)(kp['pressed'],'_')))

                    # update the text
                    Update(txt, 'text', Get('fk_cur_text'))

        # log if anything was there and not complete
        If(Get('fk_cur_text')!='',
           Set('fk_responses',
               Get('fk_responses').append(Ref(dict)(first_key_time=Get('fk_first_time'),
                                                    enter_key_time=0.0,
                                                    response=Get('fk_cur_text'),
                                                    response_num=-1))))
           # Log(first_key_time=Get('fk_first_time'),
           #     enter_key_time=0.0,
           #     response=Get('fk_cur_text'),
           #     response_num=-1))
        
        # remove the text cause we're done
        Unshow(txt)

        # Make the responses available
        Set(Ref(self,'responses'), Get('fk_responses'), eval_var=False)

        # pop off self as parent
        self.__exit__(None,None,None)


if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    from state import Parallel, Loop, Func, Debug
    from video import Show
    from dag import DAG

    exp = Experiment()

    Wait(.5)

    fk = FreeKey(Text('XXXXXX',font_size=24), max_resp=1)
    Debug(responses=fk['responses'])
    
    Show(Text('Done', font_size=32),2.0)

    fk = FreeKey(Text('??????',font_size=24))
    Debug(responses=fk['responses'])

    Wait(1.0, stay_active=True)

    exp.run()
