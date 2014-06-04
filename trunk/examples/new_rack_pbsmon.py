#! /usr/bin/env python
#
# This version of pbsmon is base on the new_rack_pbsmon.py
# 
# Authors:
#   Bas van der Vlies
#   Dennis Stam
#
#      SVN Info:
#              $Id$
#              $URL$
#

"""
specifying hostnames:
  To specify a range use the [] to indicate a range, a couple of examples:

  The first five nodes of rack 16
      - gb-r16n[1-5]

  The first five nodes and node 12 and 18 of rack 16 to 20
      - gb-r[16-20]n[1-5,12,18]

  The first five nodes de in rack 16 with padding enabled
      - gb-r[16]n[01-5]

The ranges ([]) are not only limited to numbers, letters can also be used.
"""

import sys
import re
import re
import types

import pbs
from PBSQuery import PBSQuery
from PBSQuery import PBSError

## This RE pattern is used for the hostrange
HOSTRANGE = r'\[([0-9az\-,]+)\]'

# Remark: When both are True, extended view is being printed
PRINT_TABLE = True
PRINT_EXTENDED = False

# Which nodes must be skipped
EXCLUDE_NODES = [ 'login' ]

# Some global OPTS
OPT_SKIP_EMPTY_RACKS = True
OPT_SERVERNAME = None

## Begin: TABLE view opts

# A node has the following syntax gb-r10n10
#  r10 is rack name -> skip one char --> gives us rack number = 10
#  n10 is node name -> skip one char --> gives us node number = 10
# Then we have to set these variables to determine automatically the 
# number of nodes and racks 
#
NODE_EXPR = "r(?P<racknr>[0-9]+)n(?P<nodenr>[0-9]+)" 

START_RACK = 1 

## End: TABLE view opts

## Begin: EXTENDED view opts

LENGTH_NODE  = 0
LENGTH_STATE = 0

EXTENDED_PATTERNS = {
    'header' : ' %-*s | %-*s | %s', 
    'row': ' %-*s | %-*s | %s',
    'line': ' %s',
    'line_char': '-',
}

## End: EXTENDED view opts

pbs_ND_single           = 'job (single)'
pbs_ND_total            = 'total'
pbs_ND_free_serial      = 'free serial'
pbs_ND_free_parallel    = 'free parallel'

PBS_STATES = {
    pbs.ND_free             : '_',
    pbs.ND_down             : 'X',
    pbs.ND_offline          : '.',
    pbs.ND_reserve          : 'R',
    pbs.ND_job_exclusive    : 'J',
    pbs.ND_job_sharing      : 'S',
    pbs.ND_busy             : '*',
    pbs.ND_state_unknown    : '?',
    pbs.ND_timeshared       : 'T',
    pbs.ND_cluster          : 'C',
    pbs_ND_single           : 'j',
    pbs_ND_free_serial      : '_',
    pbs_ND_free_parallel    : '_',
    pbs_ND_total            : ' '
}

## Color support?
import curses
curses.setupterm()
if curses.tigetnum("colors") > 8:
    TERMINAL_COLOR=True
else:
    TERMINAL_COLOR=False

####
## Rewriting the print function, so it will work with all versions of Python
def _print(*args, **kwargs):
    '''A wrapper function to make the functionality for the print function the same for Python2.4 and higher'''
    ## First try if we are running in Python3 and higher
    try:
        Print = eval('print')
        Print(*args, **kwargs)
    except SyntaxError:
        ## Then Python2.6 and Python2.7
        try:
            D = dict()
            exec('from __future__ import print_function\np=print', D)
            D['p'](*args, **kwargs)
            del D
        ## Finally Python2.5 or lower
        except SyntaxError:
            del D
            fout    = kwargs.get('file', sys.stdout)
            write   = fout.write
            if args:
                write(str(args[0]))
                sep = kwargs.get('sep', ' ')
                for arg in args[1:]:
                    write(sep)
                    write(str(a))
                write(kwargs.get('end', '\n'))

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def compare_lists(list_a, list_b):
    return not any(x not in list_b for x in list_a)

## Import argparse here, as I need the _print function
try:
    import argparse
except ImportError:
    _print('Cannot find argparse module', file=sys.stderr)
    sys.exit(1)

####
## BEGIN functions for hostrange parsing
def l_range(start, end):
    '''The equivalent for the range function, but then with letters, uses the ord function'''
    start = ord(start)
    end   = ord(end)
    rlist = list()

    ## A ord number must be between 96 (a == 97) and 122 (z == 122)
    if start < 96 or start > 122 and end < 96 or end > 122:
        raise Exception('You can only use letters a to z')
    ## If start is greater then end, then the range is invalid
    elif start > end:
        raise Exception('The first letter must be smaller then the second one')
    ## Just revert the ord number to the char
    for letter in range(start, end + 1):
        rlist.append(chr(letter))
    return rlist

def return_range(string):
    '''This function will return the possible values for the given ranges'''

    ## First check if the first char is valid
    if string.startswith(',') or string.startswith('-'):
        raise Exception('Given pattern is invalid, you can\'t use , and - at the beginning')

    numbers_chars        = list()
    equal_width_length  = 0

    ## First splitup the sections (divided by ,)
    for section in string.split(','):
        ## Within a section you can have a range, max two values
        chars = section.split('-')
        if len(chars) == 2:
            ## When range is a digit, simply use the range function
            if chars[0].isdigit() and chars[1].isdigit():
                ## Owke, check for equal_width_length
                if chars[0][0] == '0' or chars[1][0] == '0':
                    if len(chars[0]) >= len(chars[1]):
                        equal_width_length = len(chars[0])
                    else:
                        equal_width_length = len(chars[1])
                ## Don't forget the +1
                numbers_chars += range(int(chars[0]), int(chars[1])+1)
            ## If one of the two is a digit, raise an exceptio
            elif chars[0].isdigit() or chars[1].isdigit():
                raise Exception('I can\'t combine integers with letters, change your range please')
            ## Else use the l_range
            else:
                numbers_chars += l_range(chars[0], chars[1])
        else:
            ## If the value of the section is a integer value, check if it has a 0
            if section.isdigit() and section[0] == '0':
                if len(section) > equal_width_length:
                    equal_width_length = len(section)
            numbers_chars.append(section)

        ## if the equal_width length is greater then 0, rebuild the list
        ## 01, 02, 03, ... 10
        if equal_width_length > 0:
            tmp_list = list()
            for number_char in numbers_chars:
                if type(number_char) is types.IntType or number_char.isdigit():
                    tmp_list.append('%0*d' % ( equal_width_length, int(number_char)))
                else:
                    tmp_list.append(number_char)
            numbers_chars = tmp_list

    return numbers_chars

def product(*args, **kwargs):
    '''Taken from the python docs, does the same as itertools.product, 
    but this also works for py2.5'''
    pools = map(tuple, args) * kwargs.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

def parse_args(args):
    rlist = list()
    for arg in args:
        parts = re.findall(HOSTRANGE, arg)
        if parts:
            ## create a formatter string, sub the matched patternn with %s
            string_format = re.sub(HOSTRANGE, '%s', arg)
            ranges = list()

            ## detect the ranges in the parts
            for part in parts:
                ranges.append(return_range(part))
            
            ## produce the hostnames
            for combination in product(*ranges):
                rlist.append(string_format % combination)
        else:
            rlist.append(arg)
    return rlist

## END functions for hostrange parsing
####

def sanitize_jobs( jobs ):

    ljobs = list()

    for job in jobs:
        ljobs.extend( re.findall( r'[0-9]+\/([0-9]+)\.*.', job ) )

    return list( set( ljobs ) )

def parse_nodename( nodename ):
    global NODE_EXPR

    parts = re.search( r'%s' % NODE_EXPR, nodename, re.VERBOSE )

    try:
        racknr = parts.group( 'racknr' )
    except Exception:
		racknr = 0

    try:
        nodenr = parts.group( 'nodenr' )
    except Exception:
        nodenr = 0

    return int( racknr ), int( nodenr )

def get_nodes( racknode=False, hosts=None ):
    global LENGTH_NODE
    global LENGTH_STATE
    global OPT_SERVERNAME

    nodes_dict = dict()

    try:
        if not OPT_SERVERNAME:
            p = PBSQuery()
        else:
            p = PBSQuery( OPT_SERVERNAME )
    except PBSError, reason:
        _print('Error: %s' % reason)
        sys.exit( -1 )

    p.new_data_structure()

    attr = [ 'state', 'jobs', 'properties' ]

    try:
        nodes = p.getnodes( attr )
    except PBSError, reason:
        _print('Error: %s' % reason)
        sys.exit( -1 )

    number_of_racks = 0
    nodes_per_rack = 0
    hosts_list = list()
    
    for node, attr in nodes.items():
        if node in EXCLUDE_NODES:
            continue

        if hosts and node not in hosts:
            continue

        if pbs.ND_down in attr.state:
            state = pbs.ND_down
        else:
            state = attr.state[ 0 ]

        state_char = PBS_STATES[ state ]

        if attr.is_free() and attr.has_job():
            state = pbs.ND_busy 
            state_char = PBS_STATES[ pbs_ND_single ]

        if not nodes_dict.has_key( node ):
            nodes_dict[ node ] = dict()

        # Setting the longest lenght
        if len( node ) > LENGTH_NODE:
            LENGTH_NODE = len( node )

        if len( state ) > LENGTH_STATE:
            LENGTH_STATE = len( state )

        if racknode:
            racknr, nodenr = parse_nodename( node )

            if racknr > number_of_racks:
                number_of_racks = racknr

            if nodenr > nodes_per_rack:
                nodes_per_rack = nodenr
            
            if not nodes_dict.has_key( racknr ):
                nodes_dict[ racknr ] = dict()

            if not nodes_dict[ racknr ].has_key( nodenr ):
                nodes_dict[ racknr ][ nodenr ] = dict()

            nodes_dict[ racknr ][ nodenr ][ 'state_char' ] = state_char
            nodes_dict[ racknr ][ nodenr ][ 'state' ] = state
        
            if attr.has_key( 'jobs' ):
                nodes_dict[ racknr ][ nodenr ][ 'jobs' ] = sanitize_jobs( attr.jobs )
            else:
                nodes_dict[ racknr ][ nodenr ][ 'jobs' ] = []

            if attr.has_key( 'properties' ):
                nodes_dict[ racknr ][ nodenr ][ 'properties' ] = attr.properties
            else:
                nodes_dict[ racknr ][ nodenr ][ 'properties' ] = []

        else:
            hosts_list.append( node )
            nodes_dict[ node ][ 'state_char' ] = state_char
            nodes_dict[ node ][ 'state' ] = state
        
            if attr.has_key( 'jobs' ):
                nodes_dict[ node ][ 'jobs' ] = sanitize_jobs( attr.jobs )
            else:
                nodes_dict[ node ][ 'jobs' ] = []

            if attr.has_key( 'properties' ):
                nodes_dict[ node ][ 'properties' ] = attr.properties
            else:
                nodes_dict[ node ][ 'properties' ] = []

    if not racknode:
        return nodes_dict, hosts_list

    return nodes_dict, number_of_racks, nodes_per_rack

def _generate_index( str ):
    index = []

    def _append( fragment, alist=index ):
        if fragment.isdigit():
            fragment = int( fragment )
        alist.append( fragment )

    prev_isdigit = str[0].isdigit()
    current_fragment = ''

    for char in str:
        curr_isdigit = char.isdigit()

        if curr_isdigit == prev_isdigit:
            current_fragment += char
        else:
            _append( current_fragment )
            current_fragment = char
            prev_isdigit = curr_isdigit

    _append( current_fragment )

    return tuple( index )

def real_sort( inlist ):
    indices = map(_generate_index, inlist )
    decorated = zip( indices, inlist )
    decorated.sort()

    return [ item for index, item in decorated ]

def print_table(properties=None):
    global START_RACK 
    global OPT_SKIP_EMPTY_RACKS

    nodes, racknr, nodenr = get_nodes( True )

    ## Code herebelow has been taken from the new_rack_pbsmon.py
    save_column = None
    
    _print()    
    _print('  ', end=' ')
    for rack in xrange( START_RACK, racknr + 1 ):
        
        if not ( rack % 10 ):
            char = '%d' % ( rack / 10 )
            save_column = char
        else:
            char = ' '

        if OPT_SKIP_EMPTY_RACKS:
            if nodes.has_key( rack ):
                if save_column:
                    char = save_column
                    save_column = None
                _print(char, end=' ')
        else:
            _print(char, end=' ')
    _print()    

    _print('  ', end=' ')
    for rack in xrange( START_RACK, racknr + 1 ):
        
        char = rack % 10
        if OPT_SKIP_EMPTY_RACKS:
            if nodes.has_key( rack ):
                _print(char, end=' ')
        else:
            _print(char, end=' ')
    _print()

    for node in xrange( 1, nodenr + 1 ):
        _print('%2d' % node, end=' ')

        for rack in xrange( START_RACK, racknr + 1 ):
            if OPT_SKIP_EMPTY_RACKS:
                if not nodes.has_key( rack ):
                    continue
            try:
                if properties and compare_lists(properties,nodes[ rack ][ node ]['properties']):
                    if TERMINAL_COLOR:
                        _print(color.GREEN + nodes[ rack ][ node ][ 'state_char' ] + color.END, end=' ')
                    else:
                        _print('M', end=' ')
                else:
                    _print(nodes[ rack ][ node ][ 'state_char' ], end=' ')
            except KeyError:
                _print(' ', end=' ')
        _print()
    _print()

def print_table_summary():
    global PBS_STATES
    global OPT_SERVERNAME

    try:
        if not OPT_SERVERNAME:
            p = PBSQuery()
        else:
            p = PBSQuery( OPT_SERVERNAME )
    except PBSError, reason:
        _print('error: %s' % reason)
        sys.exit(-1)

    # get the state of the nodes
    attr = [ 'state', 'jobs', 'properties' ]
    try:
        nodes = p.getnodes(attr)
    except PBSError, reason:
        _print('error: %s' % reason)
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

        state = node['state'][ 0 ]

        state_char = PBS_STATES[state]
        count_states[state] += 1
        count_states[pbs_ND_total] += 1

        if node.is_free():                          # can happen for single CPU jobs
            if node.has_job():
#               _print('TD: %s' % nodename, node)
                state_char = PBS_STATES[pbs_ND_single]
                count_states[pbs.ND_free] -=  1
                count_states[pbs_ND_single] += 1
            else:
                if  'infiniband' in node['properties']:
                    count_states[pbs_ND_free_parallel] +=  1 
                elif  'ifiniband' in node['properties']:
                    count_states[pbs_ND_free_serial] +=  1 
                #else:
                #   count_states[pbs_ND_free_serial] +=  1 
                
#       print_('TD: %s %s' % (nodename, state_char))
        dummy = nodename.split('-')
        if len( dummy ) > 1:
            node_dict[dummy[1]] = state_char
        else:
            node_dict[dummy[0]] = state_char

    legend = PBS_STATES.keys()
    legend.sort()

    n = 0
    for state in legend:
        _print('  %s  %-13s : %-5d' % (PBS_STATES[state], state, count_states[state]), end=' ')

        n = n + 1
        if not (n & 1):
            _print()

def print_extended(hosts=None, properties=None):
    global LENGTH_NODE
    global LENGTH_STATE 
    global EXTENDED_PATTERNS
    
    nodes, ihosts = get_nodes( hosts=hosts )
    row_header = EXTENDED_PATTERNS[ 'header' ] % ( ( LENGTH_NODE + 2 ), 'Node', ( LENGTH_STATE + 2 ), 'State', 'Jobs' )
    LENGTH_ROW = len( row_header )

    rows_str = list()
    ihosts = real_sort( ihosts )

    for node in ihosts:
        attr = nodes[ node ]

        if properties and not compare_lists(properties, attr['properties']):
            continue

        row_str = EXTENDED_PATTERNS[ 'row' ] % ( ( LENGTH_NODE + 2 ), node, ( LENGTH_STATE + 2 ), attr[ 'state' ], ','.join( attr[ 'jobs' ] ) )

        if len( row_str ) > LENGTH_ROW:
            LENGTH_ROW = len( row_str )

        rows_str.append( row_str )

    _print()
    _print(row_header)
    _print(EXTENDED_PATTERNS[ 'line' ] % ( EXTENDED_PATTERNS[ 'line_char' ] * LENGTH_ROW ))
    _print('\n'.join( rows_str ))
    _print()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )

    parser.add_argument('nodes', metavar='NODES', nargs='*', type=str)
    parser.add_argument( "-t", "--table", dest="table", action="store_true", help="Show an table", default=PRINT_TABLE )
    parser.add_argument( "-l", "--list", dest="extended", action="store_true", help="Show node rows with state and jobinfo", default=PRINT_EXTENDED )
    parser.add_argument( "-s", "--summary", dest="summary", action="store_true", help="Display a short summary", default=False )
    parser.add_argument( "-a", "--all", dest="summary", action="store_true", help="Display a short summary" )
    parser.add_argument( "-w", "--wide", dest="wide", action="store_true", help="Wide display for node status ( only when -t is used )" )
    parser.add_argument( "-S", "--servername", dest="servername", help="Change the default servername", default=None )
    parser.add_argument( "-p", "--properties", dest="properties", help="Show nodes with property, you can use more than 1 property by using , (this is always een and) ie. -p infiniband,mem64gb", default=None)
    parser.add_argument('--version', action='version', version=pbs.version)

    args = parser.parse_args()

    if args.nodes:
        args.nodes = parse_args(args.nodes)

    if args.servername:
        OPT_SERVERNAME = args.servername

    if args.wide:
        OPT_SKIP_EMPTY_RACKS = False

    if args.nodes:
        args.extended = True

    if args.extended and PRINT_TABLE:
        args.table = False

    if args.table and PRINT_EXTENDED:
        args.extended = False

    if args.properties:
        args.properties = [ item.strip() for item in args.properties.split(',') ]

    if args.extended:
        print_extended(args.nodes, args.properties) 
    elif args.table:
        print_table(args.properties)
    else:
        _print('Something is wrong, bye!', file=sys.stderr)
        sys.exit( -1 )

    if args.summary:
        print_table_summary()
