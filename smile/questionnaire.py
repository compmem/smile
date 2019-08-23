#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from video import WidgetState
from clock import clock
from state import NotAvailable
from log import LogWriter
from scale import scale as s

from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
import os

class _Questionnaire(StackLayout):
    loq = ListProperty([{'type': "TITLE",
                         'question': "SMILE QUESTIONNAIRE"}])
    columns = NumericProperty(2)
    click_and_drag = BooleanProperty(False)
    quest_font_size = NumericProperty(20)
    ans_font_size = NumericProperty(17)
    default_height = NumericProperty(150)
    space = NumericProperty(100)
    column_ratio = ListProperty([.4, .6])
    results = ListProperty([])

    def __init__(self, width=None, height=None, y=0, **kwargs):
        if width == None:
            width = Window.width
        if height == None:
            height = Window.height
        super(_Questionnaire, self).__init__(orientation='lr-tb',
                                             bottom=y,
                                             size=(width, height), **kwargs)
        self.questions = []
        self.MC_List = []
        self.CA_List = []
        self.TI_List = []
        self.CT_List = []
        self.LI_List = []
        self.y = y
        self.width = self.get_width()

    def get_width(self, *args):
        return self.width

    def _continue(self):
        temp_dict = {"question_type":"",
                     "question":"",
                     "ans":""}
        res = []
        for thing in self.TI_List:
            td = temp_dict.copy()
            td.update({"question":thing['quest'],
                       "ans":str(thing["widget"].text),
                       "question_type":"TI"})
            res.append(td)
        for thing in self.CA_List:
            td = temp_dict.copy()
            ans_list = []
            for thing2 in thing:
                ans_list.append(thing2["widget"].active)
            td.update({"question":thing[0]['quest'],
                       "ans_state":ans_list,
                       "question_type":"CA"})
            res.append(td)
        for thing in self.MC_List:
            td = temp_dict.copy()
            ans_list = []
            for thing2 in thing:
                ans_list.append(thing2["widget"].state == "down")
            td.update({"question":thing[0]['quest'],
                       "ans_state":ans_list,
                       "question_type":"MC"})
            res.append(td)
        for thing in self.CT_List:
            td = temp_dict.copy()
            td.update({"question":thing['quest'],
                       "ans":thing["widget"].value,
                       "question_type":"CT"})
            res.append(td)
        for thing in self.LI_List:
            td = temp_dict.copy()
            ans_list = []
            for thing2 in thing:
                ans_list.append(thing2["widget"].active)
            td.update({"question":thing[0]['quest'],
                       "ans_state":ans_list,
                       "question_type":"LI"})
            res.append(td)

        self.results = res


    def start(self):
        CA_Count = 0
        MC_Count = 0
        LI_Count = 0
        scrlv = ScrollView(size_hint=(1., 0.95))
        if self.click_and_drag == False:
            self.scroll_type = ['bars']
        if self.columns == 1:
            layout2 = GridLayout(cols=1, size_hint_y=None,
                                 row_default_height=self.default_height,
                                 row_force_default=True, spacing=self.space)
        else:
            layout2 = GridLayout(cols=2, size_hint=(1., None), spacing=self.space,
                                 row_default_height=self.default_height,
                                 row_force_default=True)
        layout2.bind(minimum_height=layout2.setter('height'))


        quest_count = 0
        for i in range (0, len(self.loq)):
            quest = self.loq[i]
            if "ans_font_size" in quest.keys():
                ans_fs = quest["ans_font_size"]
            else:
                ans_fs = self.ans_font_size

            if "quest_font_size" in quest.keys():
                quest_fs = quest["quest_font_size"]
            else:
                quest_fs = self.quest_font_size

            if not quest["type"] == "TITLE":
                quest_count = quest_count + 1
                if "halign" not in quest.keys():
                    quest["halign"] = 'center'
                btn = Label(text=str(quest_count) + ". " + quest["question"],
                            size_hint_y=None, valign='middle',
                            size_hint_x=self.column_ratio[0],
                            font_size=quest_fs, halign=quest["halign"],
                            markup=True)
                btn.text_size=(self.column_ratio[0]*self.width*.95, None)
                layout2.add_widget(btn)

            if quest["type"] == "TI":
                textinput = TextInput(size_hint_x=self.column_ratio[1],)
                layout2.add_widget(textinput)
                self.TI_List.append({"number":i, "quest":quest["question"],
                                     "widget":textinput})


            elif quest["type"] == "CA":
                CA_Count = CA_Count + 1
                self.CA_List.append([])
                blayout = FloatLayout(size_hint_x=self.column_ratio[1],)
                points = quest["ans"]
                numPoints = len(points)
                if numPoints == 1:
                    L1 = Label(text=points[0],
                               pos_hint={'center_x':.5, 'center_y':.5},
                               font_size=ans_fs,
                               markup=True)
                    C1 = CheckBox(pos_hint={'center_x':L1.pos_hint['center_x'],
                                            'center_y':L1.pos_hint['center_y'] - .2})
                    blayout.add_widget(L1)
                    blayout.add_widget(C1)
                    self.CA_List[CA_Count - 1].append({"number":i,
                                                       "quest":quest["question"],
                                                       "label":L1.text, "widget":C1})
                else:
                    for j in range(numPoints):
                        L1 = Label(text=points[j],
                                   pos_hint={'center_x':.25 + float(j)/(2*(numPoints - 1)),
                                             'center_y':.5},
                                   font_size=ans_fs,
                                   markup=True)
                        C1=CheckBox(pos_hint={'center_x':L1.pos_hint['center_x'],
                                              'center_y':L1.pos_hint['center_y'] - .2},
                                    size_hint=(0, 0), size=(25, 25))
                        blayout.add_widget(L1)
                        blayout.add_widget(C1)
                        self.CA_List[CA_Count - 1].append({"number":i,
                                                           "quest":quest["question"],
                                                           "label":L1.text,
                                                           "widget":C1})
                layout2.add_widget(blayout)

            elif quest["type"] == "MC":
                MC_Count = MC_Count + 1
                self.MC_List.append([])
                blayout = BoxLayout(orientation='horizontal',
                                    size_hint_x=self.column_ratio[1],)
                for j in range(0, len(quest["ans"])):
                    tb = ToggleButton(text=quest["ans"][j],
                                      font_size=ans_fs,
                                      group=quest["question"],
                                      valign='middle',
                                      halign='center')
                    #tb.text_size = tb.size
                    blayout.add_widget(tb)
                    self.MC_List[MC_Count - 1].append({"number":i,
                                                       "quest":quest["question"],
                                                       "label":tb.text,
                                                       "widget":tb})
                layout2.add_widget(blayout)

            elif quest["type"] == "CT":
                points = quest["ans"]
                numPoints = len(points)
                FL = FloatLayout(size_hint=(self.column_ratio[1], 1),
                                 pos_hint={'center_x':.5,
                                           'center_y':.5})
                my_slider = Slider(min=int(quest["min"]), max=int(quest["max"]),
                                   value=(int(quest["min"]) + int(quest["max"]))/2,
                                   size_hint=(.5, None),
                                   pos_hint={'center_x':.5, 'center_y':.5})
                if numPoints == 1:
                    L1 = Label(text=points[0],
                               pos_hint={'center_x':.5, 'center_y':.7},
                               font_size=ans_fs,
                               markup=True)
                    FL.add_widget(L1)
                else:
                    for j in range(numPoints):
                        L1 = Label(text=points[j],
                                   pos_hint={'center_x':.25 + float(j)/(2*(numPoints - 1)),
                                             'center_y':.7},
                                   font_size=ans_fs,
                                   markup=True)
                        FL.add_widget(L1)

                FL.add_widget(my_slider)
                layout2.add_widget(FL)
                self.CT_List.append({"number":i, "quest":quest["question"],
                                     "widget":my_slider})

            elif quest["type"] == "LI":
                LI_Count = LI_Count + 1
                self.LI_List.append([])
                blayout = FloatLayout(size_hint_x=self.column_ratio[1])
                points = quest["ans"]
                numPoints = len(points)
                if numPoints == 1:
                    L1 = Label(text=points[0],
                               pos_hint={'center_x':.5, 'center_y':.5},
                               font_size=ans_fs,
                               markup=True)
                    C1 = CheckBox(pos_hint={'center_x':L1.pos_hint['center_x'],
                                            'center_y':L1.pos_hint['center_y'] - .2},
                                  group=quest["question"])
                    blayout.add_widget(L1)
                    blayout.add_widget(C1)
                    self.LI_List[LI_Count - 1].append({"number":i,
                                                       "quest":quest["question"],
                                                       "widget":C1})
                else:
                    for j in range(numPoints):
                        L1 = Label(text=points[j],
                                   pos_hint={'center_x':float(j + 1)/(numPoints + 1),
                                             'center_y':.5},
                                   font_size=ans_fs,
                                   markup=True)
                        C1 = CheckBox(pos_hint={'center_x':L1.pos_hint['center_x'],
                                                'center_y':L1.pos_hint['center_y'] - .2},
                                      size_hint=(0, 0), size=(25, 25),
                                      group=quest["question"])
                        blayout.add_widget(L1)
                        blayout.add_widget(C1)
                        self.LI_List[LI_Count - 1].append({"number":i,
                                                           "quest":quest["question"],
                                                           "widget":C1})
                layout2.add_widget(blayout)

            elif quest["type"] == "TITLE":
                if "halign" not in quest.keys():
                    quest["halign"] = 'center'
                btn = Label(text=str(quest["text"]), size_hint_y=None,
                            valign='middle', font_size=quest_fs,
                            size_hint_x=self.column_ratio[0],
                            halign=quest["halign"], markup=True)
                btn.text_size = (.95*self.width/2, None)
                dummy = Label(text="", size_hint_x=self.column_ratio[1])
                layout2.add_widget(btn)
                layout2.add_widget(dummy)

            else:
                layout2.add_widget(Label(text="hi", font_size=ans_fs))

        layout2.add_widget(Label(text="", size_hint_x=self.column_ratio[0],))
        layout2.add_widget(Label(text="", size_hint_x=self.column_ratio[1],))
        scrlv.add_widget(layout2)
        self.add_widget(scrlv)

    def slider_change(self, s, instance, value):
        if value >= 0:
        #this to avoid 'maximum recursion depth exceeded' error
            s.value = value


class Questionnaire(WidgetState.wrap(_Questionnaire)):
    def __init__(self, name="QLOG", **kwargs):
        super(Questionnaire, self).__init__(**kwargs)
        self._questionnaire = NotAvailable
        self.__name = name

    def show(self):
        self._widget.start()
        super(Questionnaire, self).show()

    def unshow(self):
        self._widget._continue()
        self._questionnaire = self._widget.results
        super(Questionnaire, self).unshow()

    def finalize(self):
        fn = "log_" + self.__name
        new_fn = self._exp.reserve_data_filename(title=fn, ext="slog")
        lw = LogWriter(filename=new_fn)
        for x in self._questionnaire:
            lw.write_record(x)
        lw.close()
        super(Questionnaire, self).finalize()

if __name__ == '__main__':
    from experiment import Experiment
    from state import Parallel, Log, UntilDone, Wait
    from video import Button, ButtonPress
    from mouse import MouseCursor

    bob2=[{'type':"TITLE",
           'text':"QUESTIONNAIRE"},
          {'type':"MC",
           'question':"How was today?",
           'ans':['very bad', 'bad', 'neither bad\nnor good', 'good', 'very good'],
           'halign':'left'
          },
          {'type':"MC",
           'question':"How satisfied are you with your life today?",
           'ans':["very\nunsatisfied", "unsatisfied", "neither\nunsatisfied\nnor satisfied", "satisfied", "very\nsatisfied"],
           'halign':'left'
          },
          {'type':"MC",
           'question':"To what extent did your activities today follow your typical daily routine?",
           'ans':["very\ndifferent", "fairly\ndifferent", "a little\ndifferent",  "mostly\nroutine",  "completely\nroutine"],
           'halign':'left'
          },
          {'type':"MC",
           'question':"How much free time did you have today?",
           'ans':["a very\nsmall amount",  "a small\namount",  "some",  "a large\namount",  "a very\nlarge amount"]
          },
          {'type':"MC",
           'question':"How much required work (academic or job) did you have today?",
           'ans':["a very\nsmall amount",  "a small\namount",  "some",  "a large\namount",  "a very\nlarge amount"],
           'halign':'left'
          },
          {'type':"MC",
           'question':"How often did you use your mobile phone?",
           'ans':["a very\nsmall amount",  "a small\namount",  "some",  "a large\namount",  "a very\nlarge amount"]
          },
          {'type':"MC",
           'question':"Did you do anything new today?",
           'ans':['No', 'Yes']
          },
          {'type':"MC",
           'question':"Did you meet anyone new today?",
           'ans':['No', 'Yes']
          },
          {'type':"MC",
           'question':"Did you eat anything new today?",
           'ans':['No', 'Yes']
          },
          {'type':"TITLE",
           'text':"For the following questions, to what degree did you experience the following emotions today?"
          },
          {'type':"MC",
           'question':"Positive",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Negative",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Good",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Bad",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Pleasant",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Unpleasant",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Happy",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always'],
          },
          {'type':"MC",
           'question':"Sad",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Afraid",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Joyful",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Angry",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          },
          {'type':"MC",
           'question':"Contented",
           'ans':['Very Rarely\nor Never', 'Rarely', 'Sometimes', 'Often', 'Very Often\nor Always']
          }
          ]
    bob = [{'type':"TI",
            'question':"To be or not to be?"},
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
            'ans': ['<10', '12', '15', '>20'],
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
            'ans': ['2'],
            'max': 10,
            'min': -10},
           {'type': "MC",
            'question': "Choose your favorite name.",
            'ans': ['Moe', 'Curly', 'Larry'],
            'group_id': 'second_ans_question'},
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
            'question': "Choose all that apply!",
            'ans': ['I am an Adult', 'I have a pet', 'I own a house'],
            'group_id': 'choose_question_one'},
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
            'group_id': 'second_li_question'},
            {'type': "TI",
             'question': "If you could do anything in the world right now, what would it be?",
             'multiline': 1}]

    exp = Experiment(background_color="GRAY")
    with Parallel():
        tt = Questionnaire(name="BOY", loq=bob2, quest_font_size=s(30),
                           ans_font_size=s(15))
        MouseCursor(blocking=False)
    with UntilDone():
        with ButtonPress():
            Button(text="Continue", width=s(600), height=s(50),
                   center_x=exp.screen.center_x, bottom=exp.screen.bottom)
    Wait(until=tt.questionnaire)
    exp.run()
