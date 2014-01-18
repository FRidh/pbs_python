## A useful dict with error codes to text
# Author: Bas van der Vlies <bas.vandervlies@surfsara.nl>
#
# SVN Info:
#	$Id: errors.py 429 2005-11-04 13:59:06Z bas $
#
errors_txt = { 
	0 : 'no error',
	15001 :	 'Unknown Job Identifier',
	15002 : 'Undefined Attribute',
	15003 : 'attempt to set READ ONLY attribute',
	15004 : 'Invalid request',
	15005 : 'Unknown batch request',
	15006 : 'Too many submit retries',
	15007 : 'No permission',
	15008 : 'access from host not allowed',
	15009 : 'job already exists',
	15010 : 'system error occurred',
	15011 : 'internal server error occurred',
	15012 : 'parent job of dependent in rte que',
	15013 : 'unknown signal name',
	15014 : 'bad attribute value',
	15015 : 'Cannot modify attrib in run state',
	15016 : 'request invalid for job state',
	15018 : 'Unknown queue name',
	15019 : 'Invalid Credential in request',
	15020 : 'Expired Credential in request',
	15021 : 'Queue not enabled',
	15022 : 'No access permission for queue',
	15023 : 'Bad user - no password entry',
	15024 : 'Max hop count exceeded',
	15025 : 'Queue already exists',
	15026 : 'incompatable queue attribute type',
	15027 : 'Queue Busy (not empty)',
	15028 : 'Queue name too long',
	15029 : 'Feature',
	15030 : 'Cannot enable queue,needs add def',
	15031 : 'Protocol (ASN.1) error',
	15032 : 'Bad attribute list structure',
	15033 : 'No free connections',
	15034 : 'No server to connect to',
	15035 : 'Unknown resource',
	15036 : 'Job exceeds Queue resource limits',
	15037 : 'No Default Queue Defined',
	15038 : 'Job Not Rerunnable',
	15039 : 'Route rejected by all destinations',
	15040 : 'Time in Route Queue Expired',
	15041 : 'Request to MOM failed',
	15042 : '(qsub) cannot access script file',
	15043 : 'Stage In of files failed',
	15044 : 'Resources temporarily unavailable',
	15045 : 'Bad Group specified',
	15046 : 'Max number of jobs in queue',
	15047 : 'Checkpoint Busy, may be retries',
	15048 : 'Limit exceeds allowable',
	15049 : 'Bad Account attribute value',
	15050 : 'Job already in exit state',
	15051 : 'Job files not copied',
	15052 : 'unknown job id after clean init',
	15053 : 'No Master in Sync Set',
	15054 : 'Invalid dependency',
	15055 : 'Duplicate entry in List',
	15056 : 'Bad DIS based Request Protocol',
	15057 : 'cannot execute there',
	15058 : 'sister rejected',
	15059 : 'sister could not communicate',
	15060 : 'req rejected -server shutting down',
	15061 : 'not all tasks could checkpoint',
	15062 : 'Named node is not in the list',
	15063 : 'node-attribute not recognized',
	15064 : 'Server has no node list',
	15065 : 'Node name is too big',
	15066 : 'Node name already exists',
	15067 : 'Bad node-attribute value',
	15068 : 'State values are mutually exclusive',
	15069 : 'Error(s) during global modification of nodes',
	15070 : 'could not contact Mom',
	15071 : 'no time-shared nodes',
	15201 : 'resource unknown',
	15202 : 'parameter could not be used',
	15203 : 'a parameter needed did not exist',
	15204 : "something specified didn't exist",
	15205 : 'a system error occured',
	15206 : 'only part of reservation made'
}

def error():
  """
  Check if there is an error, if so fetch the error message string. 
  It says more then a number!
  """
  e = get_error()
  if errors_txt.has_key(e):
     return (e, errors_txt[e])
  else:
     return (e, "Could not find a text for this error, uhhh")
