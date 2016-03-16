from state import Parallel, UntilDone, If, Elif, Else, Loop, Subroutine
from video import TextInput, Slider, Rectangle, Label, Button, ButtonPress, ToggleButton
from video import WidgetState

def_text_input_height = 60
min_marg_dist = 40



"""

TEXT INPUT
==========

type : "TI"
question : string
    Text to be displayed as the question
multiline : int
    Number of lines the Text Input Widget should visually have


CONTINUUM
=========

type : "CT"
question : string
    Text to be displayed as the question
ans : list
    List of 3 string answers for the Continuum. ans[0] is the Minimum and on the
    left, ans[1] is in the Median and in the middle, ans[2] is the Maximum and
    on the right. Set any ans[0], ans[1], or ans[2] to None.


MULTIPLE CHOICE
===============

type : "MC"
question : string
    Text to be displayed as the question.
ans : list
    List of 2 or more answers for the multipl choice question.
group_id : string
    A string to identify this MC from any other. Must be unique

CHECK BOXES
===========





"""







@Subroutine
def Questionaire(self,
                 list_of_questions,
                 multi_page=False,
                 title = "SMILE Questionnaire",
                 height=None,
                 width=None,
                 x=None,
                 y=None):
    self.loq = list_of_questions
    self.answers=[]

    #Process the Input Variables
    with If(x == None):
        self.x = 0
    with Else():
        self.x = x
    with If(y == None):
        self.y = 0
    with Else():
        self.y = y
    with If(width == None):
        self.width = self.exp.screen.width
    with Else():
        self.width = width
    with If(height == None):
        self.height = self.exp.screen.height
    with Else():
        self.height = height


    with If(multi_page):
        self.i = 0
        with Parallel():
            rc = Rectangle(color='GRAY', top=self.exp.screen.top, width=width,
                           height=self.exp.screen.height)
            with UntilDone():
                with Loop(conditional=(self.i<Ref(len,self.loq))):
                    #If it is a Text Input Question
                    Wait(.2)
                    with If(self.loq[self.i]['type']=='TI'):
                        #If the participant hasn't answered this question already.
                        with If(self.i == Ref(len,self.answers)):
                            with Parallel():
                                tilb1 = Label(text=self.loq[self.i]['question'], left=rc.left + 40,
                                              top=rc.top - 40, text_size=[rc.width - 80, None])
                                ti1 = TextInput(text=self.loq[self.i]['ans'][0], left=rc.left + 60,
                                                top=tilb1.bottom - 40, width=rc.width-120,
                                                height=self.loq[self.i]['multiline']*def_text_input_height)
                            with UntilDone():
                                with ButtonPress() as tibp1:
                                    Button(text='Previous', bottom=rc.bottom + 20,
                                           left=rc.left + 40, name='prev')
                                    Button(text='Continue', bottom=rc.bottom + 20,
                                           right=rc.right - 40, name='cont')
                                self.answers += [{'text':ti1.text}]
                                with If((tibp1.pressed=='prev') & (self.i != 0)):
                                    self.i = self.i - 1
                                with Elif(tibp1.pressed=='cont'):
                                    self.i = self.i + 1

                        with Else():
                            with Parallel():
                                tilb2 = Label(text=self.loq[self.i]['question'], left=rc.left + 40,
                                              top=rc.top - 40, text_size=[rc.width - 80, None])
                                ti2 = TextInput(text=self.answers[self.i]['text'], left=rc.left + 60,
                                                top=tilb2.bottom - 40, width=rc.width-120,
                                                height=self.loq[self.i]['multiline']*def_text_input_height)
                            with UntilDone():
                                with ButtonPress() as tibp2:
                                    Button(text='Previous', bottom=rc.bottom + 20,
                                           left=rc.left + 40, name='prev')
                                    Button(text='Continue', bottom=rc.bottom + 20,
                                           right=rc.right - 40, name='cont')
                                #NOTE : Change this when we have a Ref.setitem()
                                self.temp1 = self.answers[:self.i]
                                self.temp3 = [{'text':ti2.text}]
                                self.temp2 = self.answers[self.i+1:]
                                self.answers = self.temp1
                                self.answers += self.temp3
                                self.answers += self.temp2
                                with If((tibp2.pressed=='prev') & (self.i != 0)):
                                    self.i = self.i - 1
                                with Elif(tibp2.pressed=='cont'):
                                    self.i = self.i + 1
                    with Elif(self.loq[self.i]['type']=='SL'):
                        with If(self.i == Ref(len,self.answers)):
                            with Parallel():
                                sllb1 = Label(text=self.loq[self.i]['question'], left=rc.left + 40,
                                              top=rc.top - 40, text_size=[rc.width - 80, None])
                                slminlb1 = Label(text=self.loq[self.i]['ans'][0], center_x=rc.left + 100,
                                                 top=sllb1.bottom - 40)
                                slmidlb1 = Label(text=self.loq[self.i]['ans'][1], center_x=self.exp.screen.center_x,
                                                 top=sllb1.bottom - 40)
                                slmaxlb1 = Label(text=self.loq[self.i]['ans'][2], center_x=rc.right - 100,
                                                 top=sllb1.bottom - 40)
                                sl1 = Slider(left=rc.left + 100, width=rc.width - 200,
                                             min=-5, max=5, value=0, top=slminlb1.bottom-5)
                            with UntilDone():
                                with ButtonPress() as slbp1:
                                    Button(text='Previous', bottom=rc.bottom + 20,
                                           left=rc.left + 40, name='prev')
                                    Button(text='Continue', bottom=rc.bottom + 20,
                                           right=rc.right - 40, name='cont')
                                self.answers += [{'value':sl1.value}]
                                with If((slbp1.pressed=='prev') & (self.i != 0)):
                                    self.i = self.i - 1
                                with Elif(slbp1.pressed=='cont'):
                                    self.i = self.i + 1
                        with Else():
                            with Parallel():
                                sllb2 = Label(text=self.loq[self.i]['question'], left=rc.left + 40,
                                              top=rc.top - 40, text_size=[rc.width - 80, None])
                                slminlb2 = Label(text=self.loq[self.i]['ans'][0], center_x=rc.left + 100,
                                                 top=sllb2.bottom - 40)
                                slmidlb2 = Label(text=self.loq[self.i]['ans'][1], center_x=self.exp.screen.center_x,
                                                 top=sllb2.bottom - 40)
                                slmaxlb2 = Label(text=self.loq[self.i]['ans'][2], center_x=rc.right - 100,
                                                 top=sllb2.bottom - 40)
                                sl2 = Slider(left=rc.left + 100, width=rc.width - 200,
                                             min=-5, max=5, value=self.answers[self.i]['value'], top=slminlb2.bottom-5)
                            with UntilDone():
                                with ButtonPress() as slbp2:
                                    Button(text='Previous', bottom=rc.bottom + 20,
                                           left=rc.left + 40, name='prev')
                                    Button(text='Continue', bottom=rc.bottom + 20,
                                           right=rc.right - 40, name='cont')
                                #NOTE : Change This when we have a Ref.setitem()
                                self.temp1 = self.answers[:self.i]
                                self.temp3 = [{'value':sl2.value}]
                                self.temp2 = self.answers[self.i+1:]
                                self.answers = self.temp1
                                self.answers += self.temp3
                                self.answers += self.temp2

                                with If((slbp2.pressed=='prev') & (self.i != 0)):
                                    self.i = self.i - 1
                                with Elif(slbp2.pressed=='cont'):
                                    self.i = self.i + 1
    with Else():
        #for row in self.loq:
        with ScrollView(width=self.width, height=self.height, x=self.x, y=self.y) as sv:
            with FloatLayout(size=sv.size, pos=sv.pos) as fl:
                with Parallel() as fullp:
                    rcf = Rectangle(color="GRAY",top=fl.top, left=fl.left,
                                   width=self.width, height=self.height)
                    self.fullcount = Ref(len,self.loq)
                    self.new_bottom = fl.bottom
                    self.height_count = 0
                    with Loop(Ref(len, self.loq)) as lp:
                        self.fullcount = self.fullcount - 1
                        self.row = Ref.getitem(self.loq, self.fullcount)
                        # FOR TEXT INPUT
                        with If(self.row['type'] == 'TI'):
                            #EDIT THIS LINE WHEN SET AND GET IS FINISHED
                            with fullp.insert():
                                tif = TextInput(left=fl.left+min_marg_dist, font_size=font_size,
                                                bottom=self.new_bottom+min_marg_dist,
                                                width=fl.width-2*min_marg_dist,
                                                height=self.row['multiline']*def_text_input_height)
                                tirec = Rectangle(color=(0.7, 0.7, 0.7, 1.0), left=fl.left+1.5*min_marg_dist,
                                                  width=fl.width - 3*min_marg_dist,
                                                  bottom=tif.top+min_marg_dist)
                                tilb = Label(text=self.row['question'], left=fl.left+2*min_marg_dist,
                                             bottom=tif.top+min_marg_dist, font_size=font_size,
                                             text_size=(fl.width- 4*min_marg_dist, None))
                            tirec.height = tilb.height
                            self.new_bottom = tilb.top
                            self.height_count = self.height_count + tilb.height + \
                                                tif.height + (2*min_marg_dist)
                        # FOR CONTINUUM
                        with Elif(self.row['type'] == 'CT'):
                            with fullp.insert():
                                slf = Slider(left=fl.left + min_marg_dist, width=fl.width - 2*min_marg_dist,
                                             min=self.row['min'], max=self.row['max'],
                                             bottom=self.new_bottom+min_marg_dist)
                                slminlbf = Label(text=self.row['ans'][0], left=slf.left,
                                                 bottom=slf.top-1.7*min_marg_dist,font_size=font_size*3/4)
                                slmidlbf = Label(text=self.row['ans'][1], center_x=slf.center_x,
                                                 bottom=slf.top-1.7*min_marg_dist, font_size=font_size*3/4)
                                slmaxlbf = Label(text=self.row['ans'][2], right=slf.right,
                                                 bottom=slf.top-1.7*min_marg_dist, font_size=font_size*3/4)
                                slrec = Rectangle(color=(0.7, 0.7, 0.7, 1.0), left=fl.left+1.5*min_marg_dist,
                                                  width=fl.width - 3*min_marg_dist,
                                                  bottom=slminlbf.top+min_marg_dist)
                                sllbf = Label(text=self.row['question'], left=fl.left+2*min_marg_dist,
                                              bottom=slminlbf.top + min_marg_dist,
                                              text_size=(fl.width - 4*min_marg_dist, None),
                                              font_size=font_size)
                            slrec.height = sllbf.height
                            self.new_bottom = sllbf.top
                            self.height_count = self.height_count + slf.height + \
                                                slminlbf.height + sllbf.height + 0.3*min_marg_dist
                        with If(self.height_count > fl.height):
                            fl.height = self.height_count
                            rcf.height = self.height_count
                            rcf.top = fl.top
