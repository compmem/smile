

from distutils.core import setup, Extension
from distutils.sysconfig import get_config_var
import os
import sys

setup(name='smile', 
      version='0.1.0',
      package_dir={"smile":"smile"},
      packages=['smile'],
      author=['Per B. Sederberg'],
      maintainer=['Per B. Sederberg'],
      maintainer_email=['psederberg@gmail.com'],
      url=['http://github.com/compmem/smile'])

