from smile.experiment import Experiment
from smile.state import Wait
from smile.video import Image
from smile.startup import InputSubject

import os


exp = Experiment(background_color="#330000", data_dir='datadirtest',
                 name='DIRTEST')
Wait(2.0)
Image(source=os.path.join("..", "smile", "face-smile.png"), duration=1.0)
Wait(1.0)
exp.run()



# WD test.
#resource_add_path('datadirtest')
exp = Experiment(background_color="#330000",
                 data_dir=os.path.join('datadirtest',
                                       'test2'),
                 name='DIRTEST2')
InputSubject()
Wait(2.0)
Image(source=os.path.join("..", "smile", "face-smile.png"), duration=1.0)
Wait(1.0)
exp.run()
