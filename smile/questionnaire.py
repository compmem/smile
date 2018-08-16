#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .video import (WidgetState, Label,
                   ToggleButton, FloatLayout, ButtonPress,
                   Button, Rectangle, TextInput, Slider)
from .state import (Loop, Parallel, If, Elif, Else, Serial,
                   Func, UntilDone, Log, Subroutine,Debug)
from .ref import Ref
import kivy.uix.scrollview
import csv
ScrollView = WidgetState.wrap(kivy.uix.scrollview.ScrollView)

def_text_input_height = 30
min_marg_dist = 20
font_size = 15
# CA : MULTIPLE CHOIC Choose All That Apply
# TI : Text Input
# MC : MULTIPLE CHOICE Choose One
# CT : Continuum Answer
# LI : Likert


def update_dict(dict1, dict2):
    dict1.update(dict2)
    return dict1


def csv2loq(filename):
    """Load a list of questions from a CSV.

    From the CSV, you can pull in a list of questions.  This CSV has
    to be formatted correctly or it will not produce the list of
    questions that you want.

    The first line of the csv are 4 columns, *question*, *ans*,
    *type*, and *multiline*.  In the type column, you must put the
    type of question that you want to display.

    TITLE : DISPLAYING A TITLE
        A choice that allows you to display a title to a participant.

    CA : MULTIPLE CHOICE Choose All That Apply
        A multiple choice question where more than one answer can be
        chosen.

    TI : Text Input
        This kind of question is a Text input question. With the
        addtion of a multi-line key, you are able to dictate how many
        lines the Text Input Widget is tall.

    MC : MULTIPLE CHOICE Choose One
        A multiple choice question Where the participant can only pick
        one answer.

    CT : Continuum Answer
        A question that displays a slider as the answer. The slider
        allows for up to 3 labels to display above it to indicate what
        each the min, max, and middle positions represent to the
        participant.

    LI : Likert
        A likert scale presented to the participant. 2 to 10 Choices,
        horizontally below the question. This type of question can be
        used to display answers horizontally, but answers may overlap
        if the strings are too long, or if the width of the
        Questionnaire is too small. Always test to see if the likert
        scale is displaying how you want it to before administering
        this questionnaire on any participants.

    For every type of question that requires more than one value in
    the *ans* catagory, you need extra rows in your csv to represent
    them. The first row of each question will have all the columns
    that it needs filled, but for all the extra values needed in
    *ans*, you need new rows that only have values in the *ans*
    column. See yoyo.csv as an example as to what this would look
    like. Also, see the Docstring for *Questionnaire* for what types
    of questions that you need extra *ans* values for.

    """
    reader = csv.DictReader(open(filename, "r"))
    loq = []
    gpidcount = 0
    try:
        nt = reader.next()
    except:
        nt = {'type': None, "ans": None, "question": None}
    while(nt['type'] != None):
        temp = {"question": nt['question'],
                "type": nt['type'],
                "ans": [],
                "group_id": 'gp_id_' + str(gpidcount)}
        gpidcount = gpidcount + 1
        if (nt['type'] == "CA") or (nt['type'] == "LI") or \
           (nt['type'] == "MC") or (nt['type'] == "CT"):
            temp['ans'] += [nt['ans']]
            nt = reader.next()
            while((nt['type'] == "") and (nt['ans'] != None)):
                temp['ans'] += [nt['ans']]
                try:
                    nt = reader.next()
                except:
                    nt = {'type': None, "ans": None, "question": None}
        elif nt['type'] == "TI":
            if nt['multiline'] == "":
                temp['multiline'] = 0
            else:
                temp['multiline'] = int(nt['multiline'])
            try:
                nt = reader.next()
            except:
                nt = {'type': None, "ans": None, "question": None}
        elif nt['type'] == "TITLE":
            try:
                nt = reader.next()
            except:
                nt = {'type': None, "ans": None, "question": None}
        loq += [temp]

    return loq


@Subroutine
def Questionnaire(self,
                  loq,
                  height=None,
                  width=None,
                  x=None,
                  y=None,
                  save_logs=True):

    """Present a number of questions to a participant

    Passing in a list of dictionairies with different keys will allow
    you to display the questions in the order that they show up in the
    list. Below you will see the parameters you can pass into this
    state, along with what keys you need for dictionaries of each type
    of equestion that can be displayed with this state.

    Parameters
    ----------
    loq : list of dictionaries
        A list of dictionaries that contain keys associated with the
        types of questions in the order you would like them
        displayed. You can also display a Title anywhere in the list
        of questions, or in multiple places, to title a section of
        questions.
    height : integer
        Height of the Questionnaire box.
    width : integer
        Width of the Questionnaire box.
    x : integer
        Bottom left x coordinate.
    y : integer
        Bottom left y coordinate.
    save_logs : boolean (default = False)
        Save out the results to a .slog file.

    Attributes
    ----------
    results : list of dictionaries
        *self.results* is the list of dictionaries containing the list
        of results for each of the questions displayed. The keys for
        each result are *question*, *answers*, *type*, and
        *index*. *question* is a string, *answers* is a list of
        answers depending on the *type* which is also a string, and
        *index* is where it appeared in the list of questions.

    Types of Questions
    ------------------
    In your loq list of dictionaries, you always need a *type*
    key. Into each *type* you pass in a string representing the type
    of question that you want to display.

    TITLE : DISPLAYING A TITLE
        A choice that allows you to display a title to a participant.
        "type" : "TITLE"
        question : string
            String representing the Title you want to display.

    CA : MULTIPLE CHOICE Choose All That Apply
        A multiple choice question where more than one answer can be chosen.

        "type" : "CA"
        "question" : string
            Question to be displayed.
        "ans" : list
            A list of strings, displayed in the order of ans[0] at the
            top and ans[-1] at the bottom, where each string is an
            answer

    TI : Text Input
        This kind of question is a Text input question. With the
        addtion of a multi-line key, you are able to dictate how many
        lines the Text Input Widget is tall.

        "type" : "CA"
        "question" : string
            Question to be displayed.
        "multiline" : integer
            A number, at least 1, that is the number of lines tall the
            text input box is.

    MC : MULTIPLE CHOICE Choose One
        A multiple choice question Where the participant can only pick
        one answer.

        "type" : "CA"
        "question" : string
            Question to be displayed.
        "ans" : list
            A list of strings, displayed in the order of ans[0] at the
            top and ans[-1] at the bottom, where each string is an
            answer
        "group_id" : string
            A unique string with no spaces to identify this question.

    CT : Continuum Answer
        A question that displays a slider as the answer. The slider
        allows for up to 3 labels to display above it to indicate what
        each the min, max, and middle positions represent to the
        participant.

        "type" : "CA"
        "question" : string
            Question to be displayed.
        "ans" : list
            A list of 3 strings, can be empty strings. ans[0] is to
            indicate what the far left value is, ans[1] is what the
            middle value is, and ans[2] is what the far right value
            is.

    LI : Likert
        A likert scale presented to the participant. 2 to 10 Choices,
        horizontally below the question. This type of question can be
        used to display answers horizontally, but answers may overlap
        if the strings are too long, or if the width of the
        Questionnaire is too small. Always test to see if the likert
        scale is displaying how you want it to before administering
        this questionnaire on any participants.

        "type" : "LI"
        "question" : string
            Question to be displayed.
        "ans" : list
            A list of 2 to 10 strings. Can be empty strings. ans[i] is
            displayed above the coorisponding radio button.
        "group_id" : string
            A unique string with no spaces to identify this question.

    """
    # Process the Input Variables
    self.loq = loq
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
    self.questions = []
    self.CA_refs = []
    self.MC_refs = []
    self.TI_refs = []
    self.CT_refs = []
    self.LI_refs = []
    self.button_area = 2*min_marg_dist

    with ScrollView(width=self.width,
                    height=self.height-self.button_area,
                    x=self.x, y=self.y+self.button_area) as sv:
        with FloatLayout(size=sv.size, x=0, y=0) as fl:
            with Parallel() as fullp:
                rcf = Rectangle(color=(0.3, 0.3, 0.3, 1.0),
                                top=fl.height, left=0,
                                width=self.width, height=self.height)
                self.fullcount = Ref(len, self.loq)
                self.new_bottom = 0.0
                self.height_count = 0

                with Serial():
                    with Loop(Ref(len, self.loq)) as lp:
                        self.fullcount = self.fullcount - 1
                        self.row = Ref.getitem(self.loq, self.fullcount)
                        self.question_info_default = {"type": "TI",
                                                      "question": "",
                                                      "multiline": 1,
                                                      "ans": [],
                                                      "group_id": "",
                                                      "max": 10,
                                                      "min": -10}
                        qfc = Func(update_dict,
                                   self.question_info_default, self.row)
                        self.question_info = qfc.result
                        self.q_type = self.question_info['type']
                        self.question = self.question_info['question']

                        with If(self.q_type == "MC"):
                            # Setup a temp list of toggle buttons
                            # then add the group_id to a list of
                            # group id's that is a postionally linked
                            # list with toggle_buttons (for Loging Later)
                            self.temp_tog_buttons = []
                            # Setup the reverse counter for displaying the
                            # Answers from the bottom up.
                            self.tog_but_count = Ref(len,
                                                     self.question_info['ans'])
                            self.current_bottom = self.new_bottom
                            with Loop(Ref(len,
                                          self.question_info['ans'])) as mcvlp:
                                # Decrement the counter
                                self.tog_but_count = self.tog_but_count - 1
                                # Get the current answer
                                self.cur_tog_but = Ref.getitem(self.question_info['ans'],
                                                               self.tog_but_count)
                                with fullp.insert() as tbinsert:
                                    # Create label to display the answer
                                    mcvlb = Label(text=self.cur_tog_but,
                                                  left=2.5*min_marg_dist,
                                                  y=self.new_bottom+min_marg_dist,
                                                  text_size=(fl.width -
                                                             4*min_marg_dist -
                                                             2.5*min_marg_dist,
                                                             None),
                                                  save_log=False)
                                    # Create Toggle button with Group_id
                                    mcvtb = ToggleButton(but_name=self.cur_tog_but,
                                                         left=min_marg_dist,
                                                         center_y=mcvlb.center_y,
                                                         width=min_marg_dist,
                                                         height=min_marg_dist,
                                                         group=self.question_info['group_id'],
                                                         save_log=False)

                                # Append the temp list of buttons
                                self.temp_tog_buttons = self.temp_tog_buttons + [tbinsert.last]
                                # Make sure the new bottom and height
                                # is updated.
                                self.new_bottom = mcvlb.top

                            # After the loop finishes, add the temp list of
                            # buttons to the Big list of lists of buttons.
                            self.MC_refs = self.MC_refs + [self.temp_tog_buttons]
                            self.questions = self.questions + \
                                             [{"answers_index": Ref(len, self.MC_refs) - 1,
                                               "question": self.question,
                                               "type": "MC",
                                               "index": self.fullcount}]
                            # Add the question to the window aswell.
                            # Add the question to the window aswell.
                            with fullp.insert():
                                mcrec = Rectangle(color=(0.2, 0.2, 0.2, 1.0),
                                                  left=1.5*min_marg_dist,
                                                  width=fl.width - 3.0*min_marg_dist,
                                                  bottom=self.new_bottom + min_marg_dist,
                                                  save_log=False)
                                mclbf = Label(text=self.question,
                                              left=2*min_marg_dist,
                                              bottom=self.new_bottom + min_marg_dist,
                                              text_size=(fl.width - 4*min_marg_dist,
                                                         None),
                                              font_size=font_size,
                                              save_log=False)
                            # Update the height of the rectangle, buttom,
                            # and height_count
                            mcrec.height = mclbf.height
                            self.new_bottom = mcrec.top
                            self.height_count = self.height_count + (mcrec.top -
                                                                     self.current_bottom)

                        with If(self.q_type == "LI"):
                            # Setup a temp list of toggle buttons
                            # then add the group_id to a list of
                            # group id's that is a postionally linked
                            # list with toggle_buttons (for Loging Later)
                            self.temp_li_buttons = []

                            # Setup the reverse counter for displaying the
                            # Answers from the bottom up.
                            self.li_but_count = Ref(len,
                                                    self.question_info['ans'])
                            self.new_but_mid = self.width
                            self.li_width_inc = self.width / (self.li_but_count
                                                              + 1)
                            self.new_temp_bottom = self.new_bottom
                            self.current_bottom = self.new_bottom
                            with Loop(Ref(len,
                                          self.question_info['ans'])) as lilp:
                                # Decrement the counter
                                self.new_but_mid = self.new_but_mid - self.li_width_inc
                                self.li_but_count = self.li_but_count - 1
                                # Get the current answer
                                self.cur_li_but = Ref.getitem(self.question_info['ans'],
                                                              self.li_but_count)
                                with fullp.insert() as liinsert:
                                    # Create Toggle button with Group_id
                                    litb = ToggleButton(but_name=self.cur_li_but,
                                                        center_x=self.new_but_mid,
                                                        bottom=self.new_bottom + min_marg_dist,
                                                        width=min_marg_dist,
                                                        height=min_marg_dist,
                                                        group=self.question_info['group_id'],
                                                        save_log=False)
                                    # Create label to display the answer
                                    lilb = Label(text=self.cur_li_but,
                                                 center_x=litb.center_x,
                                                 font_size=font_size*3/4,
                                                 y=litb.top + (0.5*min_marg_dist),
                                                 save_log=False)
                                # Append the temp list of buttons
                                self.temp_li_buttons = self.temp_li_buttons + [liinsert.first]

                                # Make sure the new bottom and
                                # height is updated.
                                with If(self.new_temp_bottom < liinsert.last.top):
                                    self.new_temp_bottom = liinsert.last.top

                            self.new_bottom = self.new_temp_bottom

                            # After the loop finishes, add the temp
                            # list of buttons to the big list of lists
                            # of buttons.

                            self.LI_refs = self.LI_refs + [self.temp_li_buttons]
                            self.questions = self.questions + [{"answers_index": Ref(len, self.LI_refs) - 1,
                                                                "question": self.question,
                                                                "type": "LI",
                                                                "index": self.fullcount}]
                            # Add the question to the window aswell.
                            with fullp.insert():
                                lirec = Rectangle(color=(0.2, 0.2, 0.2, 1.0),
                                                  left=1.5*min_marg_dist,
                                                  width=fl.width - 3.0*min_marg_dist,
                                                  bottom=self.new_bottom+min_marg_dist,
                                                  save_log=False)
                                lilbf = Label(text=self.question,
                                              left=2*min_marg_dist,
                                              bottom=self.new_bottom+min_marg_dist,
                                              text_size=(fl.width - 4*min_marg_dist, None),
                                              font_size=font_size,
                                              save_log=False)
                            # Update the height of the rectangle, buttom, and height_count
                            lirec.height = lilbf.height
                            self.new_bottom = lirec.top
                            self.height_count = self.height_count + (lirec.top -
                                                                     self.current_bottom)

                        with Elif(self.q_type == "CA"):
                            # Setup a temp list of toggle buttons
                            self.temp_ca_buttons = []
                            # Setup the reverse counter for displaying the
                            # Answers from the bottom up.
                            self.ca_but_count = Ref(len,
                                                    self.question_info['ans'])
                            self.current_bottom = self.new_bottom
                            with Loop(Ref(len,
                                          self.question_info['ans'])) as cavlp:
                                # Decrement the counter
                                self.ca_but_count = self.ca_but_count - 1
                                # Get the current answer
                                self.cur_ca_but = Ref.getitem(self.question_info['ans'],
                                                              self.ca_but_count)
                                with fullp.insert() as cainsert:
                                    # Create label to display the answer
                                    cavlb = Label(text=self.cur_ca_but,
                                                  left=2.5*min_marg_dist,
                                                  y=self.new_bottom + min_marg_dist,
                                                  text_size=(fl.width -
                                                             4*min_marg_dist -
                                                             2.5*min_marg_dist,
                                                             None),
                                                  save_log=False)

                                    # Create Toggle button with Group_id
                                    cavtb = ToggleButton(but_name=self.cur_ca_but,
                                                         left=min_marg_dist,
                                                         center_y=cavlb.center_y,
                                                         width=min_marg_dist,
                                                         height=min_marg_dist,
                                                         save_log=False)

                                # Append the temp list of buttons
                                self.temp_ca_buttons = self.temp_ca_buttons + [cainsert.last]
                                # Make sure the new bottom and
                                # height is updated.
                                self.new_bottom = cavlb.top

                            # After the loop finishes, add the temp list of
                            # buttons to the Big list of lists of buttons.
                            self.CA_refs = self.CA_refs + [self.temp_ca_buttons]

                            self.questions = self.questions + [Ref(dict,
                                                               answers_index=Ref(len,self.CA_refs) - 1,
                                                               question=self.question, type="CA",
                                                               index=self.fullcount)]
                            # Add the question to the window aswell.
                            with fullp.insert():
                                carec = Rectangle(color=(0.2, 0.2, 0.2, 1.0),
                                                  left=1.5*min_marg_dist,
                                                  width=fl.width - 3.0*min_marg_dist,
                                                  bottom=self.new_bottom+min_marg_dist,
                                                  save_log=False)
                                calbf = Label(text=self.question,
                                              left=2*min_marg_dist,
                                              bottom=self.new_bottom + min_marg_dist,
                                              text_size=(fl.width - 4*min_marg_dist,
                                                         None),
                                              font_size=font_size,
                                              save_log=False)
                            # Update the height of the rectangle, buttom,
                            # and height_count
                            carec.height = calbf.height
                            self.new_bottom = carec.top
                            self.height_count = self.height_count + (carec.top -
                                                                     self.current_bottom)

                        with Elif(self.q_type == "TI"):
                            with fullp.insert() as tiinsert:
                                tif = TextInput(left=min_marg_dist,
                                                font_size=font_size,
                                                bottom=self.new_bottom + min_marg_dist,
                                                width=fl.width - 2*min_marg_dist,
                                                height=self.question_info['multiline'] * def_text_input_height,
                                                save_log=False)

                                tirec = Rectangle(color=(0.2, 0.2, 0.2, 1.0),
                                                  left=1.5*min_marg_dist,
                                                  width=fl.width - 3*min_marg_dist,
                                                  bottom=tif.top+min_marg_dist,
                                                  save_log=False)
                                tilb = Label(text=self.question,
                                             left=2*min_marg_dist,
                                             bottom=tif.top+min_marg_dist,
                                             font_size=font_size,
                                             text_size=(fl.width - 4*min_marg_dist,
                                                        None),
                                             save_log=False)
                            self.TI_refs = self.TI_refs + [tiinsert.first]
                            self.questions = self.questions + [{"answers_index": Ref(len, self.TI_refs) - 1,
                                                                "question": self.question,
                                                                "type": "TI",
                                                                "index": self.fullcount}]
                            tirec.height = tilb.height
                            self.new_bottom = tilb.top
                            self.height_count = self.height_count + \
                                                tilb.height + \
                                                tif.height + (2*min_marg_dist)

                        with Elif(self.q_type == "CT"):
                            with fullp.insert() as ctinsert:
                                slf = Slider(left=min_marg_dist,
                                             width=fl.width - 2*min_marg_dist,
                                             min=self.question_info['min'],
                                             max=self.question_info['max'],
                                             bottom=self.new_bottom + min_marg_dist,
                                             save_log=False)
                                slminlbf = Label(text=self.question_info['ans'][0],
                                                 left=slf.left,
                                                 bottom=slf.top - 1.7*min_marg_dist,
                                                 font_size=font_size*3/4,
                                                 save_log=False)
                                slmidlbf = Label(text=self.question_info['ans'][1],
                                                 center_x=slf.center_x,
                                                 bottom=slf.top - 1.7*min_marg_dist,
                                                 font_size=font_size*3/4,
                                                 save_log=False)
                                slmaxlbf = Label(text=self.question_info['ans'][2],
                                                 right=slf.right,
                                                 bottom=slf.top - 1.7*min_marg_dist,
                                                 font_size=font_size*3/4,
                                                 save_log=False)
                                slrec = Rectangle(color=(0.2, 0.2, 0.2, 1.0),
                                                  left=1.5*min_marg_dist,
                                                  width=fl.width - 3*min_marg_dist,
                                                  bottom=slminlbf.top + min_marg_dist,
                                                  save_log=False)
                                sllbf = Label(text=self.question,
                                              left=2*min_marg_dist,
                                              bottom=slminlbf.top + min_marg_dist,
                                              text_size=(fl.width - 4*min_marg_dist,
                                                         None),
                                              font_size=font_size,
                                              save_log=False)
                            self.CT_refs = self.CT_refs + [ctinsert.first]
                            self.questions = self.questions + [{"answers_index": Ref(len, self.CT_refs) - 1,
                                                                "question": self.question,
                                                                "type": "CT",
                                                                "index": self.fullcount}]
                            slrec.height = sllbf.height
                            self.new_bottom = sllbf.top
                            self.height_count = (self.height_count +
                                                 slf.height +
                                                 slminlbf.height +
                                                 sllbf.height +
                                                 0.3*min_marg_dist)

                        with Elif(self.q_type == "TITLE"):
                            with fullp.insert():
                                fulltitlb = Label(text=self.question,
                                                  bottom=self.new_bottom + 2*min_marg_dist,
                                                  font_size=font_size * 1.5,
                                                  center_x=self.width/2)
                            self.height_count = (self.height_count +
                                                 (fulltitlb.top - self.new_bottom) +
                                                 4*min_marg_dist)
                            self.new_bottom = fulltitlb.top + 2*min_marg_dist

                    with If((self.height_count > rcf.height)):
                        fl.height = self.height_count+50.
                        rcf.height = self.height_count+50.
                        rcf.top = fl.top

    with UntilDone():
        with ButtonPress():
            Rectangle(color=(.25, .25, .25, 1.), left=sv.left,
                      height=self.button_area,
                      width=self.width, y=self.y)
            Button(text="Continue", left=self.x + .5*min_marg_dist,
                   top=sv.bottom - .25*min_marg_dist,
                   height=self.button_area*.75)
        self.group_counter = 0
        self.results = []

        with Loop(self.questions) as question:
            with If(question.current['type'] == "TI"):
                self.results = self.results + [{"question": question.current['question'],
                                                "type": "TI", "index": question.current['index'],
                                                "answers": [{"ans": "text_input_value",
                                                             "value": self.TI_refs[question.current['answers_index']].text}]
                                                }]
            with Elif(question.current['type'] == "CT"):
                self.results = self.results + [{"question": question.current['question'],
                                                "type": "CT", "index": question.current['index'],
                                                "answers": [{"ans": "slider_value",
                                                             "value": self.CT_refs[question.current['answers_index']].value}]
                                                }]
            with Elif(question.current['type'] == "MC"):
                self.mc_temp_answers_list = []
                with Loop(self.MC_refs[question.current['answers_index']]) as mc_loop_ref:
                    self.mc_temp_answers_list = self.mc_temp_answers_list + [{"ans": mc_loop_ref.current.but_name,
                                                                              "value": mc_loop_ref.current.state == 'down'}]
                self.results = self.results + [{"question": question.current['question'],
                                                "type": "MC", "index": question.current['index'],
                                                "answers": self.mc_temp_answers_list}]
            with Elif(question.current['type'] == "CA"):
                self.ca_temp_answers_list = []
                with Loop(self.CA_refs[question.current['answers_index']]) as ca_loop_ref:
                    self.ca_temp_answers_list = self.ca_temp_answers_list + [{"ans": ca_loop_ref.current.but_name,
                                                                              "value": ca_loop_ref.current.state == 'down'}]
                self.results = self.results + [{"question": question.current['question'],
                                                "type": "CA", "index": question.current['index'],
                                                "answers": self.ca_temp_answers_list}]
            with Elif(question.current['type'] == "LI"):
                self.li_temp_answers_list = []
                with Loop(self.LI_refs[question.current['answers_index']]) as li_loop_ref:
                    self.li_temp_answers_list = self.li_temp_answers_list + [{"ans": li_loop_ref.current.but_name,
                                                                              "value": li_loop_ref.current.state == 'down'}]
                self.results = self.results + [{"question" :question.current['question'],
                                                "type": "LI", "index": question.current['index'],
                                                "answers": self.li_temp_answers_list}]

        with If(save_logs):
            Log(self.results,
                name="questionnaire",)


if __name__ == "__main__":
    from .mouse import MouseCursor
    bob = [{'type': "TITLE",
            'question': "SMILE QUESTIONNAIRE"},
           {'type': "LI",
            'question': "How Happy Are You?",
            'ans': ['Not Happy',
                    '', '',
                    'Meh',
                    '', '',
                    'Happy'],
            'group_id': 'first_question'},
           {'type': "LI",
            'question': "How Old are you?",
            'ans': ['<10', '12', '15', '<20'],
            'group_id':'second_li_question'},
           {'type': "LI",
            'question': "To be or not to be?",
            'ans': ['That is the Question.',
                    'To be is to do.',
                    'To do is to be.'],
            'group_id': 'THIRD_li_question'},
           {'type': "CT",
            'question': "How many years have you lived in your current home?",
            'ans': ['1', '5', '10'],
            'max': 5,
            'min': -5},
           {'type': "CT",
            'question': "Where left is Too much, and right is too little, and middle is just right, how much does your car cost?",
            'ans': ['', '', ''],
            'max': 10,
            'min': -10},
           {'type': "TI",
            'question': "Choose your favorite name.",
            'ans': ['Moe', 'Curly', 'Larry'],
            'group_id': 'second_ans_question'},
           {'type': "TI",
            'question': "If you could do anything in the world right now, what would it be?",
            'multiline': 1},
           {'type': "TI",
            'question': "Tell me about your life.",
            'multiline': 3},
           {'type': "TI",
            'question': "Tell me about your breakfest",
            'multiline': 2},
           {'type': "MC",
            'question': "Choose your Favorite Jim Carry Movie!",
            'ans': ['Eternal Sunshine of the Spotless Mind',
                    'Yes Man',
                    'A Series of Unfortunate Events',
                    'I Love You, Phillip Morris!'],
            'group_id': 'third_ans_question'},
           {'type': "CA",
            'question': "Choose the all that apply!",
            'ans': ['I am an Adult', 'I have a pet', 'I own a house'],
            'group_id': 'choose_question_one'},
           {'type': "TITLE",
            'question': "SMILE QUESTIONNAIRE 2 "},
           {'type': "LI",
            'question': "How Happy is your family?",
            'ans': ['Not Happy',
                    '', '',
                    'Meh',
                    '', '',
                    'Happy'],
            'group_id': 'first_question'},
           {'type': "LI",
            'question': "How Old is your mother?",
            'ans': ['10', '12', '15', '20'],
            'group_id': 'second_li_question'}]

    from .experiment import Experiment
    exp = Experiment()
    with Parallel():
        tt = Questionnaire(loq=bob,
                           height=800,
                           width=600,
                           x=50, y=50,)
        MouseCursor(blocking=False)
    exp.run()