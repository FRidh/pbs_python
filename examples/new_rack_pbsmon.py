#! /usr/bin/env python
#
#	pbsmon	WJ104
#
#	* added START_RACK BvdV
#	* added Total, pbs_serial_free and pbs_parallel free, BvdV
#
#	Hint: set ts=4
#
#	SVN Info:
#		$Id$
#
import os
import sys
import string
import getopt
import re

import pbs
from PBSQuery import PBSQuery
from PBSQuery import PBSError

# A node has the following syntax gb-r10n10
#  r10 is rack name -> skip one char --> gives us rack number = 10
#  n10 is node name -> skip one char --> gives us node number = 10
# Then we have to set these variables to determine automatically the 
# number of nodes and racks 
#
NODE_EXPR = re.compile(r"""
	(?P<racknr>r[0-9]+)
	(?P<nodenr>n[0-9]+)
""", re.VERBOSE) 

SKIP_CHARS_RACK = 1 
SKIP_CHARS_NODE = 1 

NODE_SPLIT_STR = '-'
NODE_STR = 'r%dn%d'





NODES_PER_RACK = 32
START_RACK = 1
N_RACKS = 43

pbs_ND_single			= 'job (single)'
pbs_ND_total			= 'total'
pbs_ND_free_serial		= 'free serial'
pbs_ND_free_parallel	= 'free parallel'

PBS_STATES = {
	pbs.ND_free				: '_',
	pbs.ND_down				: 'X',
	pbs.ND_offline			: '.',
	pbs.ND_reserve			: 'R',
	pbs.ND_job_exclusive	: 'J',
	pbs.ND_job_sharing		: 'S',
	pbs.ND_busy				: '*',
	pbs.ND_state_unknown	: '?',
	pbs.ND_timeshared		: 'T',
	pbs.ND_cluster			: 'C',
	pbs_ND_single			: 'j',
	pbs_ND_free_serial		: '_',
	pbs_ND_free_parallel	: '_',
	pbs_ND_total			: ' '
}

# command line options
OPT_NODESTATUS = 1
OPT_SUMMARY = 0
OPT_WIDE = 0
OPT_SERVERNAME = None


def determine_limits(nodes):
	"""
	Determiine the the limits of the cluster:
	  - How many racks are in the cluster
	  - What is the max amount of nodes per rack
	"""
	rack_max = node_max = 0
	for id in nodes:
		result = NODE_EXPR.search(id)
		if result:

			number = int(result.group('racknr')[SKIP_CHARS_RACK:])
			if number > rack_max:
				rack_max = number

			number = int(result.group('nodenr')[SKIP_CHARS_NODE:])
			if number > node_max:
				node_max = number

	return (rack_max+1, node_max+1)
 		

def pbsmon(server = None):
	global NODES_PER_RACK, N_RACKS, PBS_STATES, OPT_WIDE

	try:
		if not server:
			p = PBSQuery()
		else:
			p = PBSQuery(server)
	except PBSError, reason:
		print 'error: %s' % reason
		sys.exit(-1)

	p.new_data_structure()

# get the state of the nodes
	attr = [ 'state', 'jobs', 'properties' ]

	try:
		nodes = p.getnodes(attr)
	except PBSError, reason:
		print 'error: %s' % reason
		sys.exit(-1)

	node_dict = {}

	number_of_racks, nodes_per_rack = determine_limits(nodes)

	for id in nodes:

		# Skip login nodes in status display
		#
		if not nodes[id].name.find('login'):
			continue

		if pbs.ND_down in nodes[id].state:
			state = pbs.ND_down
		else:
			state = nodes[id].state[0]

		state_char = PBS_STATES[state]

		#print 'TD: ', nodes[id].name, nodes[id].is_free() ,nodes[id].has_job()

		if nodes[id].is_free() and nodes[id].has_job():		# single job
			#print 'TD: %s' % id, nodes[id]
			state_char = PBS_STATES[pbs_ND_single]

		#print 'TD: %s %s' % (nodename, state_char)

		# Remove the prefix of the node, eg gb-r15n1 --> r15n1
		#
		dummy = string.split(nodes[id].name, NODE_SPLIT_STR)
		node_dict[dummy[1]] = state_char



# print header lines
	print '  ',
	for rack in xrange(START_RACK, number_of_racks):
		if not (rack % 10):
			print '%d' % (rack / 10),
		else:
			print ' ',

		if OPT_WIDE:
			print '',
	print

	print '  ',
	for rack in xrange(START_RACK, number_of_racks):
		print '%d' % (rack % 10),
		if OPT_WIDE:
			print '',
	print

# print nodes with r%dn%d naming scheme
	for node_nr in xrange(1, nodes_per_rack):
		print '%2d' % node_nr,

		for rack in xrange(START_RACK, number_of_racks):
			node_name = NODE_STR %(rack, node_nr)

			if node_dict.has_key(node_name):
				print '%s' % node_dict[node_name],

				del node_dict[node_name]
			else:
				print ' ',
		
			if OPT_WIDE:
				print '',

		print

	print

# any other nodes?
	arr = node_dict.keys()
	if arr:
		arr.sort()

		for node in arr:
			print '%s %s' % (node, node_dict[node])

		print


#
#	summary() counts the number of nodes in a particular state
#
def pbsmon_summary(server = None):
	global NODES_PER_RACK, N_RACKS, PBS_STATES

	try:
		if not server:
			p = PBSQuery()
		else:
			p = PBSQuery(server)
	except PBSQuery.PBSError, reason:
		print 'error: %s' % reason
		sys.exit(-1)

# get the state of the nodes
	attr = [ 'state', 'jobs', 'properties' ]
	try:
		nodes = p.getnodes(attr)
	except PBSError, reason:
		print 'error: %s' % reason
		sys.exit(-1)

	node_dict = {}

	count_states = {}
	for key in PBS_STATES.keys():
		count_states[key] = 0

	for nodename, node in nodes.items():

		# Skip login nodes in status display
		#
		if not nodename.find('login'):
			continue

		state = node['state']
		if string.find(state, ',') >= 0:			# multiple states for a node?
			state = string.split(state, ',')[-1]

		state_char = PBS_STATES[state]
		count_states[state] += 1
		count_states[pbs_ND_total] += 1

		if node.is_free():							# can happen for single CPU jobs
			if node.has_job():
#				print 'TD: %s' % nodename, node
				state_char = PBS_STATES[pbs_ND_single]
				count_states[pbs.ND_free] -=  1
				count_states[pbs_ND_single] += 1
			else:
				if  node['properties'].find('infiniband') >= 0:
					count_states[pbs_ND_free_parallel] +=  1 
				elif  node['properties'].find('gigabit') >= 0:
					count_states[pbs_ND_free_serial] +=  1 
				#else:
				#	count_states[pbs_ND_free_serial] +=  1 
				
#		print 'TD: %s %s' % (nodename, state_char)
		dummy = string.split(nodename, '-')
		node_dict[dummy[1]] = state_char

	legend = PBS_STATES.keys()
	legend.sort()

	n = 0
	for state in legend:
		print '  %s  %-13s : %-5d' % (PBS_STATES[state], state, count_states[state]),

		n = n + 1
		if not (n & 1):
			print


def pbsmon_legend():
	global PBS_STATES

	legend = PBS_STATES.keys()
	legend.sort()

	n = 0
	for state in legend:
		if state == 'total':
			continue

		print '  %s  %-20s' % (PBS_STATES[state], state),

		n = n + 1
		if not (n & 1):
			print


def usage():
	global PROGNAME

	print 'usage: %s [options]' % PROGNAME
	print '%s displays the status of the nodes in the batch system' % PROGNAME
	print
	print 'Options:'
	print '  -h, --help             Show this information'
	print '  -s, --summary          Display only a short summary'
	print '  -a, --all              Display both status and summary'
	print '  -w, --wide             Wide display for node status'
	print '  -S, --server=<server>  Use a different PBS/Torque server'
	print
	print 'Legend:'

	pbsmon_legend()
	

def getopts():
	global PROGNAME, OPT_NODESTATUS, OPT_SUMMARY, OPT_WIDE, OPT_SERVERNAME

	if len(sys.argv) <= 1:
		return

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hsawS:', ['help','summary', 'all', 'wide', 'server='])
	except getopt.error, reason:
		print '%s: %s' % (PROGNAME, reason)
		usage()
		sys.exit(1)

	except getopt.GetoptError, reason:
		print '%s: %s' % (PROGNAME, reason)
		usage()
		sys.exit(1)

	except:
		usage()
		sys.exit(1)

	server = None
	errors = 0

	for opt, arg in opts:
		if opt in ('-h', '--help', '-?'):
			usage()
			sys.exit(1)

		if opt in ('-s', '--summary'):
			OPT_SUMMARY = 1
			OPT_NODESTATUS = 0
			continue

		if opt in ('-a', '--all'):
			OPT_SUMMARY = 1
			OPT_NODESTATUS = 1
			continue

		if opt in ('-w', '--wide'):
			OPT_WIDE = 1
			continue

		if opt in ('-S', '--server'):
			OPT_SERVERNAME = arg
			continue

		print "%s: unknown command line option '%s'" % (PROGNAME, opt)
		errors = errors + 1

	if errors:
		usage()
		sys.exit(1)


if __name__ == '__main__':
	PROGNAME = os.path.basename(sys.argv[0])
	getopts()

	if OPT_NODESTATUS:
		pbsmon(OPT_SERVERNAME)

	if OPT_SUMMARY:
		print 'Summary:'
		pbsmon_summary(OPT_SERVERNAME)

	sys.exit(0)

# EOB

