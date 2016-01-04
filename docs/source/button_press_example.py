
from smile.common import *

exp = Experiment()

#From here you can see setup for a ButtonPress state.
with ButtonPress(correct='left', duration=5) as bp:
    #correct allows you to name the button that will end up being the correct
    #answer to this particular ButtonPress
    MouseCursor()
    Button(name='left', text='left', left=exp.screen.left, bottom=exp.screen.bottom)
    Button(name='right', text='right', right=exp.screen.right, bottom=exp.screen.bottom)
    Label(text='PRESS THE LEFT BUTTON FOR A CORRECT ANSWER!')
Wait(.2)
with If(bp.correct):
    Label(text='YOU PICKED CORRECT', color='GREEN', duration=1)
with Else():
    Label(text='YOU WERE DEAD WRONG', color='RED', duration=1)
exp.run()
