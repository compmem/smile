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
    def __init__(self, filename, field_names):
        self._field_names = field_names
        self._file = gzip.open(filename, "wb")
        self._pickler = cPickle.Pickler(self._file, -1)
        self._pickler.dump(field_names)

    def write_record(self, data):
        """Call this funciton to write a single row to the .slog file.
        
        Parameters
        ----------
        data : list 
            This is a list of dictionaries where the keys are the field names that you
            are writing out to the .slog file. 
        
        """
        record = [data[field_name] for field_name in self._field_names]
        self._pickler.dump(record)

    def close(self):
        """Run this funciton once you are done writing to the .slog        
        """
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

        # read until one pickle is done
        self._unpickler = cPickle.Unpickler(self._file)
        self._field_names = tuple(self._unpickler.load())

    @property
    def field_names(self):
        return self._field_names

    def read_record(self):
        """Returns a dicitionary with the field names as keys.
        """
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
        self.close()


def _unwrap(d, prefix='', depth=0):
    new_item = []
    to_remove = []
    for k, v in d:
    	key = prefix + k
        if depth > 0:
            new_item.append((key, v))
        elif isinstance(v, dict):
            new_item.extend(_unwrap(v.items(), prefix=key+'_', depth=depth+1))
        elif type(v) in (tuple, list):
            new_subitem = []
            for j, subv in enumerate(v):
                new_subitem.append((str(j), subv))
            new_item.extend(_unwrap(new_subitem, prefix=key+'_',
                                    depth=depth+1))
        else:
            new_item.append((key, v))
    return new_item


def log2csv(log_filename, csv_filename):
    """Converts a slog to a CSV.
    
    This state is can be used outside of a SMILE experiment, and is an easy way
    to get your .slog formated file into an easily readable format. This function 
    is mostly used when you pass **-c** into the command line when running an 
    experiment. 
    
    Parameters
    ----------
    log_filename : string
        The path to the .slog file
    csv_filename : string
        The path to the new .csv file this function is about to create.
    """
    colnames = []
    reader = LogReader(log_filename)
    for record in reader:
        for fieldname, value in _unwrap([(name, record[name]) for name in
                                          reader.field_names]):
            if fieldname not in colnames:
                colnames.append(fieldname)
                                    
    with open(csv_filename, 'wb') as fout:
        dw = csv.DictWriter(fout, fieldnames=list(colnames))
        dw.writeheader()
        for record in LogReader(log_filename):
            dw.writerow(dict(_unwrap(record.items())))

