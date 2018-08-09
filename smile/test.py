from smile.common import *

font1=40

exp=Experiment(background_color="GRAY")

with Parallel():
    lbl21 = Label(text="You will be presented with a second list of words. Press 'F' if you are absolutely sure you've seen the word before, either in the first list or this one. Press 'G' if you're slightly sure you've seen the word before, either in the first list or this one. Press 'J' if you're absolutely sure you've never seen the word before. Press 'H' if you're slightly sure you've never seen the word before.",
    font_size=font1, text_size=(exp.screen.width*2/3, None), multiline=True)
    lbl22 = Label(text="Press any key when ready", font_size=font1, top=lbl21.bottom)
exp.run()
