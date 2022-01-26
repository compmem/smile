from smile.common import Experiment, Wait, Label, Image, Debug, Ref
from os.path import join
import sys

fp = join('C:\\Users\\caboodle513\\code\\beegica\\smile\\smile', 'face-smile.png')

exp = Experiment()
Debug(fp=fp, clean_fp=Ref(exp.clean_path, fp))
Image(source=fp, duration=1.0)
exp.run()
