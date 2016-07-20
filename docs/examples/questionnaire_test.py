from smile.common import *
from smile.questionnaire import csv2loq

exp = Experiment(resolution=(600,500))
with Parallel():
    tt = Questionnaire(loq = Ref(csv2loq, "questionnaire_example.csv"),
                       height = exp.screen.height, width = exp.screen.width,
                       x = 0, y=0,)
    MouseCursor()
Log(tt.results)

exp.run()