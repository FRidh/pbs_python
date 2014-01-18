#  PBS python interface
#  Author: Bas van der Vlies <bas.vandervlies@surfsara.nl>
#  Date  : 27 Feb 2002
#  Desc. : This is python wrapper class for getting the resource
#          mom values.
#
# CVS info
# $Id: resmom.py,v 1.6 2002/10/21 14:14:47 sscpbas Exp $
# $Date: 2002/10/21 14:14:47 $
# $Revision: 1.6 $
#
import string
import types

# Default linux resources to get from the mom
#
default_linux_res = [   
    "availmem",	    # available memory size in KB
    "ideal_load",	# static ideal_load value
    "loadave",      # the current load average
    "max_load",	    # static max_load value
    "ncpus",        # number of cpus 
    "physmem",      # physical memory size in KB
    "resi",		    # resident memory size for a pid or session in KB
    "totmem",	    # total memory size in KB
    "walltime",	    # wall clock time for a pid
]

# Default irix6 resources to get from the mom
#
default_irix6_res = [   
    "availmem",	# available memory size in KB
    "loadave",      # the current load average
    "ncpus",        # number of cpus
    "physmem",      # physical memory size in KB
    "resi",		# resident memory size for a pid or session in KB
    "walltime",	# wall clock time for a pid
    "quota",	# quota information (sizes in KB)
]

default_mom_res = [   
    "arch",		# the architecture of the machine
    "uname",	# the architecture of the machine
    "cput",		# cpu time for a pid or session
    "idletime",	# seconds of idle time
    "mem",		# memory size for a pid or session in KB
    "sessions",	# list of sessions in the system
    "pids",         # list of pids in a session
    "nsessions",	# number of sessions in the system
    "nusers",	# number of users in the system
    "size",		# size of a file or filesystem
    "host",		# Name  of host on which job should be run 
    "nodes",	# Number and/or type of nodes to be reserved for exclusive use by the job
    "other",	# Allows a  user  to  specify  site  specific  information
    "software",	# Allows a user to specify software required by the job
]

def check_resp(dict, str):
  """
  Check the daemon response. If we have no permission to
  query the values then we got a 'None' response. Else
  if we supplied a keyword that does not exits we get a
  '?' response
  """
  if not str:
    return
  
  ## Value can contain the '=' char :-(
  #  
  l =  string.split(str, '=')
  key = string.strip(l[0])
  if len(l) > 2:
    val = string.strip( '='.join(l[1:]) )
  else:
    val = string.strip(l[1])

  key = string.strip(key)
  val = string.strip(val)

  # Did we got a valid response
  #
  if not val[0] == '?':
    dict[key] = val

def use_default_keywords(id, d):
  """
  Get the default values from the mom daemon
  """
  for res in default_mom_res:
    addreq(id, res)
    resp = getreq(id)
    check_resp(d, resp)

  # Do not proceed if we have an empty dictionary
  #
  if not d:
    return

  if d['arch' ] == 'linux':
    for res in default_linux_res:
      addreq(id, res)
      resp = getreq(id)
      check_resp(d, resp)

def use_user_keywords(id, d, l):
  for res in l:
    if type(res) is types.StringType:
      addreq(id, res)
      resp = getreq(id)
      check_resp(d, resp)
    else:
      raise TypeError, 'Expected a string got %s :%s' %(type(res), res) 

def get_mom_values(id, list = None):
  """
  This function will query the mom with a default resmon keywords
  and 'arch' depended keywords. Supported archs are:
    linux
    irix6
  User can also supply their own list of keywords as second parameter.
  arguments:
    id   : connection number with mom daemon on a node
    list : optional parameter. If supplied then use this. A list
           of mom keywords.
  """

  d = {}
  if not list:
    use_default_keywords(id, d)
  else:
    use_user_keywords(id, d , list)
     
  return d
