#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


import cPickle
import gzip

class LogWriter(object):
    def __init__(self, filename, field_names):
        self._field_names - field_names
        self._file = gzip.open(filename, "wb")
        self._pickler = cPickl.Pickler(self._file, -1)
        self._pickler.dump(field_names)

    def write_record(self, data):
        record = [data[field_name] for field_name in self.field_names]
        self._pickler.dump(record)

    def close(self):
        self._file.close()

class LogReader(object):
    def __init__(self, filename):
        self._file = gzip.open(filename, "rb")
        self._unpickler = cPickle.Unpickler(self._file)
        self._field_names = self._unpickler.load()

    def read_record(self):
        try:
            return dict(zip(self._field_names, self._unpickler.load()))
        except EOFError:
            return None

    def close(self):
        self._file.close()

    def __iter__(self):
        record = self.read_record()
        while record is not None:
            yield record
            record = self.read_record()



import yaml
import csv
#import sys

# set up a dumper that does not do anchors or aliases
if hasattr(yaml,'CSafeDumper'):
    Dumper = yaml.CSafeDumper
else:
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
def load_yaml(yaml_file, **append_cols):
    # load the dictlist
    dictlist = yaml.load(open(yaml_file,'r'))
    if dictlist is None:
        return []
    for i in range(len(dictlist)):
        dictlist[i].update(append_cols)
    return dictlist

def unwrap(d, prefix=''):
    """
    Process the items of a dict and unwrap them to the top level based
    on the key names.
    """
    new_item = {}
    for k in d:
       	# add prefix
    	key = prefix+k
        
        # see if dict
        if isinstance(d[k],dict):
            new_item.update(unwrap(d[k],prefix=key+'_'))
            continue

        # see if tuple
        if isinstance(d[k],tuple):
            # turn into indexed dict
            tdict = {}
            for j in range(len(d[k])):
                tdict[str(j)] = d[k][j]
            new_item.update(unwrap(tdict,prefix=key+'_'))
            continue

        # just add it in
        new_item[key] = d[k]

    return new_item
    
def yaml2dl(yaml_file, **append_cols):
    # load in the yaml as a dict list
    dl = load_yaml(yaml_file, **append_cols)

    # loop over each kv pair and unwrap it
    for i in xrange(len(dl)):
        dl[i] = unwrap(dl[i])

    return dl

def yaml2csv(dictlist, csv_file, **append_cols):
    # see if dictlist is a yaml file
    if isinstance(dictlist,str):
        # assume it's a file and read it in
        # get the unwraped dict list
        dictlist = yaml2dl(dictlist, **append_cols)
    dl = dictlist

    if len(dl) == 0:
        return

    # get all unique colnames
    colnames = []
    for i in range(len(dl)):
        for k in dl[i]:
            if not k in colnames:
                colnames.append(k)
                      
    # write it out
    with open(csv_file, 'wb') as fout:
        # create file and write header
        dw = csv.DictWriter(fout, fieldnames=colnames)
        dw.writeheader()
        # continue on to write data
        dw.writerows(dl)

