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
import csv

class LogWriter(object):
    """An object that handles the writing of .slog files. 
    
    *LogWriter* is what we use to write data to a .slog file. The *Log* state 
    relies heavily on this object.  
    
    Parameters
    ----------
    filename : string
        The filename that you would like to write to. Must end in .slog. 
    field_names : list 
        A list of strings that contains the fields you wish to write. 
    """

    def __init__(self, filename):
        self._file = gzip.open(filename, "wb")
        self._pickler = cPickle.Pickler(self._file, -1)

    def write_record(self, data):
        """Call this funciton to write a single row to the .slog file.
        
        Parameters
        ----------
        data : list 
            This is a list of dictionaries where the keys are the field names that you
            are writing out to the .slog file. 
        
        """
        # data must be a dict
        if not isinstance(data, dict):
            raise ValueError("data to log must be a dict instance.")
        self._pickler.dump(data)
        self._pickler.clear_memo()

    def close(self):
        self._file.close()


class LogReader(object):
    """An object that handles reading from .slog files. 
    
    Passing in a filename, by calling **ReadRecord** you can read on row from the
    .slog file. 
    
    Parameters
    ----------
    filename : string
        The name of the .slog that you wish to read from.
        
    """
    def __init__(self, filename):
        self._file = gzip.open(filename, "rb")

        # set up the unpickler
        self._unpickler = cPickle.Unpickler(self._file)

    def read_record(self):
        """Returns a dicitionary with the field names as keys.
        """
        try:
            return self._unpickler.load()
        except EOFError:
            return None

    def close(self):
        self._file.close()

    def __iter__(self):
        record = self.read_record()
        while record is not None:
            yield record
            record = self.read_record()
        self.close()


def _unwrap(d, prefix=''):
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
            new_item.update(_unwrap(d[k],prefix=key+'_'))
            continue

        # see if tuple/list
        if isinstance(d[k],(tuple,list)):
            # turn into indexed dict
            tdict = {}
            for j in range(len(d[k])):
                tdict[str(j)] = d[k][j]
            new_item.update(_unwrap(tdict,prefix=key+'_'))
            continue

        # just add it in
        new_item[key] = d[k]

    return new_item


def log2csv(log_filename, csv_filename, **append_columns):
    """Convert a slog to a CSV."""
    # get the set of colnames
    colnames = append_columns.keys()
    for record in LogReader(log_filename):
        for fieldname in _unwrap(record):
            if fieldname not in colnames:
                colnames.append(fieldname)
                
    # loop again and write out to file
    with open(csv_filename, 'wb') as fout:
        # open CSV and write header
        dw = csv.DictWriter(fout, fieldnames=list(colnames))
        dw.writeheader()

        # loop over log entries
        for record in LogReader(log_filename):
            # unwrap dict to top level
            record = _unwrap(record)

            # append cols after unwraping
            record.update(append_columns)

            # handle unicode
            record = dict((k, v.encode('utf-8')
                           if isinstance(v, unicode)
                           else v)
                          for k, v in record.iteritems())

            # write it out
            dw.writerow(record)

