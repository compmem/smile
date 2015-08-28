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
    def __init__(self, filename, field_names):
        self._field_names = field_names
        self._file = gzip.open(filename, "wb")
        self._pickler = cPickle.Pickler(self._file, -1)
        self._pickler.dump(field_names)

    def write_record(self, data):
        record = [data[field_name] for field_name in self._field_names]
        self._pickler.dump(record)

    def close(self):
        self._file.close()


class LogReader(object):
    def __init__(self, filename):
        self._file = gzip.open(filename, "rb")
        self._unpickler = cPickle.Unpickler(self._file)
        self._field_names = tuple(self._unpickler.load())

    @property
    def field_names(self):
        return self._field_names

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

    #with open(csv_filename, 'wb') as fout:
    #    reader = LogReader(log_filename)
    #    dw = csv.DictWriter(fout, fieldnames=reader.field_names)
    #    dw.writeheader()
    #    for record in reader:
    #        dw.writerow(record)

#...
