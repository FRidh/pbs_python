#!/usr/bin/env python
#
# Author: Bas van der Vlies <bas.vandervlies@surfsara.nl>
#
# $Id: setup.py 531 2010-04-07 13:13:29Z bas $

import sys
import os

from distutils.core import setup, Extension 
from distutils.spawn import spawn

## Always unlink previous links
#
try:
    os.unlink('pbs.py')
    os.unlink('pbs_wrap.c')
except OSError:
    pass

swig_cmd = [ 'swig', "-python", "-shadow" , 'pbs.i' ]
spawn(swig_cmd, verbose=2)
os.rename('pbs_wrap.c', 'pbs_wrap_2.1.c')
os.rename('pbs.py', 'pbs_2.1.py')

swig_cmd = [ 'swig', "-DTORQUE_2_4","-python", "-shadow" , 'pbs.i' ]
spawn(swig_cmd, verbose=2)
os.rename('pbs_wrap.c', 'pbs_wrap_2.4.c')
os.rename('pbs.py', 'pbs_2.4.py')


# The location of the pbs libraries. If left blank
# then we try to find out where the libraries are
#
PBS_LIB_DIR=''
NEW_BUILD_SYSTEM=1

if not PBS_LIB_DIR:
  for dir in ['/usr/local/lib', '/opt/pbs/usr/lib', '/usr/lib/torque', '/usr/lib' ]:
    dummy_new = os.path.join(dir, 'libtorque.so')
    dummy_old = os.path.join(dir, 'libpbs.a')
    if os.path.exists(dummy_new):
      PBS_LIB_DIR=dir
      break
    elif os.path.exists(dummy_old):
      PBS_LIB_DIR=dir
      NEW_BUILD_SYSTEM=0
      break

if not PBS_LIB_DIR:
  print 'Please specify where the PBS libraries are!!'
  print 'edit setup.py and fill in the PBS_LIB_DIR variable'

# Do we use the old or new build system
#
if NEW_BUILD_SYSTEM:
  LIBS = ['torque']
else:
  LIBS = ['log', 'net', 'pbs']

cmd = 'pbs-config --version'
output = os.popen(cmd).readline()
l = output.split('.')
major_version = '.'.join(l[0:2])
print major_version


if major_version in [ '2.3', '2.4']:
	has_new_functions = '1'
	os.symlink('pbs_wrap_2.4.c', 'pbs_wrap.c')
	os.symlink('pbs_2.4.py', 'pbs.py')
else:
	has_new_functions = '0'
	os.symlink('pbs_wrap_2.1.c', 'pbs_wrap.c')
	os.symlink('pbs_2.1.py', 'pbs.py')
	
setup ( name = 'pbs_python',
        version = '2.9.8-beta',
	description = 'pbs python interface',
	author = 'Bas van der Vlies',
	author_email = 'basv@sara.nl',
	url = 'http://www.sara.nl/beowulf',

	# extra_path = 'pbs',
        # package_dir = { '' : 'src' }, 
	py_modules = [ 'pbs' ],
	
	ext_modules = [ 
	  Extension( '_pbs', ['pbs_wrap.c'] ,
	  library_dirs = [ PBS_LIB_DIR ], 
	  define_macros =  [ ('TORQUE_2_4', None) ],
	  libraries = LIBS
	  ) 
	]
)

