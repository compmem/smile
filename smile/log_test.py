from common import *

exp = Experiment(background_color="GRAY", debug=True)

label=Label(text="Hello World", duration=1.0)
#Debug(z=Ref(str,15.0001))
'''with Meanwhile():
    Wait(until=label.appear_time, name=Ref(str,15.001))
    #kp = KeyPress(keys='K',correct_resp=["K"], base_time=label.appear_time['time'])
    kp = KeyPress(keys=['K'], correct_resp='K', base_time=label.appear_time['time'])'''
#exp.lst=["brandon", "helen", "nathan", "kathryn", "jeremy"]
with Loop(["helen", "brandon", "nathan"]) as trial:
    #Debug(TRIALNAME=str(trial))
    Debug(x=trial.current)
    Label(text=trial.current, duration=.01, name=trial.current)
    Log(name=trial.current,
        i=trial.i)
#exp.variable = kp.correct
'''Debug(x=kp.correct)
Log(name=kp.correct, correct=kp.correct)'''
#a = kp.correct
#Log(name=a, correct=kp.correct)
#Label(text="BOB", duration=2.)

exp.run()

"""
flankr blocks

ipython
Reading a slog file 
python
from log import log2dl
import pandas
a = pandas.DataFrame(log2dl("path\\filename")) (Make sure \\ --> \\)
a
a['name']
"""

#C:\\Users\\limhe\\OneDrive\\School\\UVa\\CompAnalyLab\\smile-master\\smile\\data\\SMILE\\test000\\20180628_100945\\log_Henlo_0.slog
#C:\\Users\\limhe\\OneDrive\\School\\UVa\\CompAnalyLab\\smile-master\\smile\\data\\SMILE\\test000\\20180628_103941

"""
('name', Ref(<type 'str'>, 15.001)),
look for code where "name" is set in the data dict
pickle.dump() writes the byte stream to the file (i.e. byte stream is a pickle representation of object)
thus, ref must be able to convert into a byte stream
OR change the ref into some string name
convert to byte stream ?
C:\\Users\\limhe\\OneDrive\\School\\UVa\\CompAnalyLab\\smile-master\\smile\\data\\SMILE\\test000\\20180705_150010
C:\\Users\\limhe\\OneDrive\\School\\UVa\\CompAnalyLab\\smile-master\\smile\\data\\SMILE\\test000\\20180705_150010
In class Log(AutoFinalizedState) in state.py

C:\\Users\\limhe\\OneDrive\\School\\UVa\\CompAnalyLab\\smile-master\\smile\\data\\SMILE\\test000\\20180705_152542
"""