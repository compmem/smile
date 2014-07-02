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

# set the allowable keys (A-Z)
asciiplus = [str(unichr(i)) for i in range(65,65+26)]
asciiplus += ['RETURN','ENTER','BACKSPACE','SPACE']

class FreeKey(Serial):
    """
    Perform free recall typed responses.
    """
    def __init__(self, txt=None, duration=10.0, base_time=None, max_resp=0,
                 parent=None, save_log=True):
        super(FreeKey, self).__init__(parent=parent, duration=duration, 
                                      save_log=save_log)

        # show the initial text
        if txt is None:
            txt = Text('??????', parent=self)
        else:
            # claim that text
            self.claim_child(txt)

        # set self as parent
        # like using with, but without the indentation
        self.__enter__()

        # save the starting text
        Set('fk_start_text',txt['shown'].text)

        # set base_time
        if base_time is None:
            base_time = txt['first_flip']['time']

        # Loop until out of time or press enter
        Set('fk_end_time', base_time+duration)
        Set('fk_cur_text','')
        with Loop(conditional=Get('fk_end_time')>Ref(gfunc=now)) as loop:
            # accept keyboard response (for remaining duration)
            kp = KeyPress(keys=asciiplus, base_time=base_time,
                          duration=Get('fk_end_time')-Ref(gfunc=now))

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
                    Log(first_key_time=Get('fk_first_time'),
                        enter_key_time=kp['press_time'],
                        response=Get('fk_cur_text'))

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
                       Set('fk_cur_text', Get('fk_cur_text')+kp['pressed']))

                    # update the text
                    Update(txt, 'text', Get('fk_cur_text'))

        # log if anything was there and not complete
        If(Get('fk_cur_text')!='',
           Log(first_key_time=Get('fk_first_time'),
               enter_key_time=0.0,
               response=Get('fk_cur_text')))
        
        # remove the text cause we're done
        Unshow(txt)

        # pop off self as parent
        self.__exit__(None,None,None)


if __name__ == '__main__':

    from experiment import Experiment, Get, Set
    from state import Parallel, Loop, Func
    from dag import DAG

    exp = Experiment()

    Wait(.5)

    FreeKey(Text('??????',font_size=24))

    Wait(1.0, stay_active=True)

    exp.run()
