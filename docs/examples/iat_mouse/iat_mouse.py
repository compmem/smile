from smile.common import *
from config import *
from gen_stim import *

#Start setting up the experiment
exp = Experiment()


#Setup the Block loop, where *block* is a
#Reference to the variable you are looping over
with Loop(BLOCKS) as block:
    #Show the instructions to the paricipant
    RstDocument(text=block.current['instruct'], base_font_size=RSTFONTSIZE, width=RSTWIDTH, height=exp.screen.height)
    with UntilDone():
        #When a KeyPress is detected, the UntilDone
        #will cancel the RstDocument state
        KeyPress()
    #Setup a loop over each Trial in a Block. *block.current* references the
    #current interation of the loop, which is a dictionary that contatins the list
    #words. *trial* will be our reference to the current word in our loop.
    with Loop(block.current['words']) as trial:
        #initialize our testing variable in Experiment Runtime
        #exp.something = something will create a Set state
        exp.mouse_test = False
        #The following is a ButtonPress state. This state works like KeyPress,
        #but instead waits for any of the buttons that are its children to be
        #press.
        with ButtonPress(correct_resp=trial.current['correct']) as bp:
            #block.current is a dictionary that has all of the information we
            #would need during each individual block, including the text that is
            #in these buttons, which differes from block to block
            Button(text=block.current['left_word'], name="left", left=0,
                   top=exp.screen.top, width = BUTTONWIDTH, height=BUTTONHEIGHT, text_size = (170, None),
                   font_size=FONTSIZE, halign='center')
            Button(text=block.current['right_word'], name="right",
                   right=exp.screen.right, top=exp.screen.top,
                   width = BUTTONWIDTH, height = BUTTONHEIGHT, text_size = (170, None),
                   font_size=FONTSIZE, halign='center')
            #Required! To see the mouse on the screen
            MouseCursor()
        #while Those buttons are waiting to be pressed, go ahead and do the
        #children of this next state, the Meanwhile
        with Meanwhile():
            #The start button that is required to be pressed before the trial
            #word is seen.
            with ButtonPress():
                Button(text="Start", bottom=exp.screen.bottom, font_size=FONTSIZE)
            #Do all of the children of a Parallel at the same time.
            with Parallel():
                #display target word
                target_lb = Label(text=trial.current['center_word'], font_size=FONTSIZE, bottom=exp.screen.bottom+100)
                #Record the movements of the mouse
                MouseRecord(name="MouseMovements")
                #Setup an invisible rectangle that is used to detect exactly
                #when the mouse starts to head toward an answer.
                rtgl = Rectangle(center=MousePos(), width=MOUSEMOVERADIUS,
                                 height=MOUSEMOVERADIUS, color=(0,0,0,0))
                with Serial():
                    #wait until the mouse leaves the rectangle from above
                    wt = Wait(until=(MouseWithin(rtgl) == False))
                    #If they waited too long to start moving, tell the experiment
                    #to display a warning message to the paricipant
                    with If(wt.event_time['time'] - wt.start_time > MOUSEMOVEINTERVAL):
                        exp.mouse_test = True
        with If(exp.mouse_test):
            Label(text="You are taking to long to move, Please speed up!",
                  font_size=FONTSIZE, color="RED", duration=WARNINGDURATION)
        #wait the interstimulus interval
        Wait(INTERTRIALINTERVAL)
        #WRITE THE LOGS
        Log(name="IAT_MOUSE",
            left=block.current['left_word'],
            right=block.current['right_word'],
            word=trial.current,
            correct=bp.correct,
            reaction_time=bp.press_time['time']-target_lb.appear_time['time'],
            slow_to_react=exp.mouse_test)
#the line required to run your experiment after all
#of it is defined above
exp.run()
