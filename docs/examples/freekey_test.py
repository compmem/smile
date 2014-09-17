#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile import *

exp = Experiment()

Show(Text("Get Ready"),duration=1.0)

Wait(.5)

FreeKey(Text('??????',font_size=24))

Wait(1.0, stay_active=True)


if __name__ == '__main__':
    #from smile.dag import DAG
    #d = DAG(exp)
    #d.write('/tmp/freekey.pdf')

    exp.run()

