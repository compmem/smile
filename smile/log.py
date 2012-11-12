#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


import yaml
import sys

# set up a dumper that does not do anchors or aliases
Dumper = yaml.SafeDumper
Dumper.ignore_aliases = lambda self, data: True
def dump(logline, stream=None):
    return yaml.dump(logline, stream, Dumper=Dumper)

# for eventually writing CSV files with headers
# from: http://stackoverflow.com/questions/2982023/writing-header-in-csv-python-with-dlictwriter
"""
from collections import OrderedDict
ordered_fieldnames = OrderedDict([('field1',None),('field2',None)])
with open(outfile,'wb') as fou:
    dw = csv.DictWriter(fou, delimiter='\t', fieldnames=ordered_fieldnames)
    dw.writeheader()
    # continue on to write data
"""
