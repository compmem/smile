#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import os
import sys
from distutils.core import setup, Extension
from distutils.sysconfig import get_config_var, get_python_lib
from distutils.dir_util import copy_tree

setup(name='smile', 
      version='0.1.0',
      package_dir={"smile":"smile"},
      packages=['smile'],
      author=['Per B. Sederberg'],
      maintainer=['Per B. Sederberg'],
      maintainer_email=['psederberg@gmail.com'],
      url=['http://github.com/compmem/smile'])


