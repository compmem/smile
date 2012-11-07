

from distutils.core import setup, Extension
from distutils.sysconfig import get_config_var
import os
import sys

setup(name='pygie', 
      version='0.0.1',
      package_dir={"pygie":"pygie"},
      packages=['pygie'],
      author=['Per B. Sederberg'],
      maintainer=['Per B. Sederberg'],
      maintainer_email=['psederberg@gmail.com'],
      url=['http://github.com/compmem/pygie'])

