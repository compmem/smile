from smile.common import *

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
        'text':"For the following questions,\nto what degree did you experience\nthe following emotions today?"
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
    tt = Questionnaire(name="BOY", loq=bob, quest_font_size=30,
                        ans_font_size=15)
    MouseCursor(blocking=False)
with UntilDone():
    with ButtonPress():
        Button(text="Continue", width=600, height=50,
                center_x=exp.screen.center_x, bottom=exp.screen.bottom)
Wait(until=tt.questionnaire)
exp.run()
