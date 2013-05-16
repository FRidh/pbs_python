#!/usr/bin/env python
#
# Author: Dennis Stam
# Date  : 6th of September 2012
#
# Tested with Python 2.5, 2.6, 2.7 (should work for 3.0, 3.1, 3.2)
#   sara_nodes uses the module argparse

## The documenation, is shown when you type --help
HELP_DESCRIPTION = '''This program is a great example what you can achieve with the pbs_python wrapper. You can use sara_nodes to change the state of a machine to offline with a reason. Several information is stored in the nodes note attribute. Information such as; date added, date last change, the username, ticket number (handy when you wan't to reference to an issue in your tracking system) and the message.'''
HELP_EPILOG = '''The format argument uses the Python string formatting. Fields that can be used are; nodename, state, date_add, date_edit, username, ticket and note. For example sara_nodes -f '%(nodename)s;%(state)s' '''

## This variable is used to sort by basename
SPLIT_SORT = r'r\d+n\d+'
## This RE pattern is used for the hostrange
HOSTRANGE = r'\[([0-9az\-,]+)\]'
## Which states are allowed to show in the print_overview
ALLOWED_STATES = set(['down', 'offline', 'unknown'])

import pbs
import PBSQuery
import re
import sys
import time
import getpass
import types

## Use the cli arguments to change the values
ARGS_QUIET      = False
ARGS_VERBOSE    = False
ARGS_DRYRUN     = False

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

## Import argparse here, as I need the _print function
try:
    import argparse
except ImportError:
    _print('Cannot find argparse module', file=sys.stderror)
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
        raise Exception('The letters must be in alphabetical order')
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
            ## If one of the two is a digit, raise an exception
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

####
## BEGIN functions for printing
def _generate_index(string):
    '''Is used to generate a index, this way we can also sort nummeric values in a string'''
    return [ int(y) if y.isdigit() else y for y in re.split(r'(\d+)', string) ]

def print_get_nodes(hosts=None):
    '''This function retrieves the information from your batch environment'''
    if ARGS_VERBOSE:
        _print('func:print_get_nodes input:%s' % str(hosts), file=sys.stderr)

    ## there are 2 possible filters, by hostname, or by state
    pbsq         = PBSQuery.PBSQuery()
    split_1     = dict()
    split_2     = dict()

    if ARGS_VERBOSE: 
        _print('func:print_get_nodes fetching node information', file=sys.stderr)
    ## We ask from the batch all nodes, and with the properties state and note
    for host, properties in pbsq.getnodes(['state', 'note']).items():
        do_host = None
        ## Check if the current host matches our criterium (given with the arguments
        ## or has the allowed state)
        if hosts and host in hosts:
            do_host = host
        elif not hosts:
            ## Do a intersection on both set's, if there is a match, then the host is allowed
            if bool(ALLOWED_STATES.intersection(set(properties.state))):
                do_host = host

        ## when we have a do_host (means matches our criterium) then sort
        ## them by basename
        if do_host:
            if SPLIT_SORT and re.findall(SPLIT_SORT, do_host):
                split_1[host] = properties
            else:
                split_2[host] = properties
    
    if ARGS_VERBOSE: 
        _print('func:print_get_nodes returning values', file=sys.stderr)
    return split_1, split_2

def print_process_dict(dictin):
    '''This function processes the data from the batch system and make it for all hosts the same layout'''
    if ARGS_VERBOSE: 
        _print('func:print_process_dict input:%s' % str(dictin), file=sys.stderr)

    line_print = list()
    if ARGS_VERBOSE: 
        _print('func:print_process_dict processing data', file=sys.stderr)

    ## Generate a list containing a dictionary, so we can use the stringformatting functionality
    ## of Python, fieldnames are: nodename, date_edit, date_add, username, ticket, note

    ## Replaced real_sort with sorted, this means from 50 lines of code to 3
    for host in sorted(dictin.keys(), key=_generate_index):
        add_dict = dict()

        add_dict['nodename'] = host
        ## Glue the state list with a ,
        add_dict['state'] = ", ".join(dictin[host]['state'] if dictin[host].has_key('state') else [])

        ## Check if the given host has a note
        note = dictin[host]['note'] if dictin[host].has_key('note') else []
        if note:
            add_dict['date_add']    = note[0]
            add_dict['date_edit']   = note[1]
            add_dict['username']    = note[2]
            add_dict['ticket']      = note[3]
            add_dict['note']        = ",".join(note[4:])

            ## Create an extra date field, combined for date_edit and date_add
            if add_dict['date_add'] and add_dict['date_edit']:
                add_dict['date'] = '%s, %s' % (add_dict['date_add'], add_dict['date_edit'])
            elif add_dict['date_add']:
                add_dict['date'] = add_dict['date_add']
            else:
                add_dict['date'] = None

        else:
            ## If there is no note, just set the variables with a empty string
            add_dict['date'] = add_dict['date_add'] = add_dict['date_edit'] = add_dict['username'] = add_dict['ticket'] = add_dict['note'] = ''

        line_print.append(add_dict)

    if ARGS_VERBOSE: 
        _print('func:print_process_dict returning values', file=sys.stderr)
    return line_print

def print_create_list(values):
    tmp_list = list()
    for pair in values:
        tmp_list.append('%-*s' % tuple(pair))
    return tmp_list

def print_overview_normal(hosts=None):
    '''Print the default overview'''
    if ARGS_VERBOSE: 
        _print('func:print_overview_normal input:%s' % str(hosts), file=sys.stderr)

    ## Determine some default values for the column width
    w_nodename = 8
    w_state = 5 
    w_date = w_username = w_ticket = w_note = w_date_add = w_date_edit = 0

    ## Get the data, make it one list, the rest first then the matched
    matched, rest = print_get_nodes(hosts)
    print_list = print_process_dict(rest)
    print_list.extend(print_process_dict(matched))

    ## Detect the max width for the columns
    for line in print_list:
        if line['nodename'] and len(line['nodename']) > w_nodename:
            w_nodename = len(line['nodename'])
        if line['state'] and len(line['state']) > w_state:
            w_state = len(line['state'])
        if line['date'] and len(line['date']) > w_date:
            w_date = len(line['date'])
        if line['date_add'] and len(line['date_add']) > w_date_add:
            w_date_add = len(line['date_add'])
        if line['date_edit'] and len(line['date_edit']) > w_date_edit:
            w_date_edit = len(line['date_edit'])
        if line['username'] and len(line['username']) > w_username:
            w_username = len(line['username'])
        if line['ticket'] and len(line['ticket']) > w_ticket:
            w_ticket = len(line['ticket'])
        if line['note'] and len(line['note']) > w_note:
            w_note = len(line['note'])

    ## The length of the full note
    w_notefull  = w_date + w_username + w_ticket + w_note

    if not ARGS_QUIET:
        show_fields = [
            [w_nodename, 'Nodename'],
            [w_state, 'State'],
        ]
        if w_date > 0:
            show_fields.append([w_date_add,'Added'])
            show_fields.append([w_date_edit,'Modified'])
            show_fields.append([w_username,'User'])
            if w_ticket > 0:
                if w_ticket < 6:
                    w_ticket = 6
                show_fields.append([w_ticket,'Ticket'])
            show_fields.append([w_note,'Note'])

        _print(' %s' % ' | '.join(print_create_list(show_fields)))
        _print('+'.join([ '-' * (show_field[0]+2) for show_field in show_fields ]))

    ## Show the information to the user
    for line in print_list:
        show_line_fields = [
            [w_nodename, line['nodename']],
            [w_state, line['state']],
        ]
        if w_date > 0:
            show_line_fields.append([w_date_add,line['date_add']])
            show_line_fields.append([w_date_edit,line['date_edit']])
            show_line_fields.append([w_username,line['username']])
            if w_ticket > 0:
                show_line_fields.append([w_ticket,line['ticket']])
            show_line_fields.append([w_note,line['note']])

        _print(' %s' % ' | '.join(print_create_list(show_line_fields)))

def print_overview_format(hosts=None, format=None):
    '''Print the information in a certain format, when you want to use it in a
    different program'''

    matched, rest = print_get_nodes(hosts)
    print_list = print_process_dict(rest)
    print_list.extend(print_process_dict(matched))

    for line in print_list:
        _print(format % line)
## END functions for printing
####

class SaraNodes(object):
    '''This class is used to communicate with the batch server'''

    ticket      = None

    def _get_current_notes(self, nodes):
        '''A function to retrieve the current message'''
        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_get_current_notes input:%s' % str(nodes), file=sys.stderr)

        pbsq = PBSQuery.PBSQuery()
        rdict = dict()

        ## We are only intereseted in the note
        for node, properties in pbsq.getnodes(['note']).items():
            if node in nodes and properties.has_key('note'):
                rdict[node] = properties['note']
        return rdict

    def _get_curdate(self):
        '''Returns the current time'''
        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_get_curdate', file=sys.stderr)
        return time.strftime('%d-%m %H:%M', time.localtime())

    def _get_uid(self, prev_uid=None):
        '''Get the username'''
        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_get_uid input:%s' % prev_uid, file=sys.stderr)
        cur_uid = getpass.getuser()
        if prev_uid and cur_uid == 'root':
            return prev_uid
        return cur_uid

    def _get_ticket(self, prev_ticket=None):        
        '''Check if we already have a ticket number'''
        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_get_ticket input:%s' % prev_ticket, file=sys.stderr)
        cur_ticket = '#%s' % self.ticket
        if prev_ticket and cur_ticket == prev_ticket:
            return prev_ticket
        elif self.ticket and self.ticket.isdigit():
            return cur_ticket
        elif self.ticket in ['c','clear','N',]:
            return ''
        elif prev_ticket:
            return prev_ticket
        return ''

    def _generate_note(self, nodes=None, note=None, append=True):
        '''Generates the node in a specific format'''
        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_generate_note input:%s,%s,%s' % (str(nodes), note, str(append)), file=sys.stderr)

        ## First step, is to get the current info of a host
        cur_data = self._get_current_notes(nodes)
        rdict = dict()

        for node in nodes:
            date_add = date_edit = username = ticket = nnote = None
            if node in cur_data.keys():
                date_add    = cur_data[node][0]
                date_edit   = self._get_curdate()
                username    = self._get_uid(cur_data[node][2])
                ticket      = self._get_ticket(cur_data[node][3])
                nnote       = ",".join(cur_data[node][4:])
            else:
                date_add = date_edit = self._get_curdate()
                username = self._get_uid()
                ticket   = self._get_ticket()
                nnote    = None

            if nnote and append and note:
                nnote = '%s, %s' % (nnote, note)
            elif note:
                nnote = note

            rdict[node] = '%s,%s,%s,%s,%s' % (date_add, date_edit, username, ticket, nnote)
        return rdict

    def do_offline(self, nodes, note):
        '''Change the state of node(s) to offline with a specific note'''

        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:do_offline input:%s,%s' % (str(nodes), note), file=sys.stderr)
        attributes          = pbs.new_attropl(2)
        attributes[0].name  = pbs.ATTR_NODE_state
        attributes[0].value = 'offline'
        attributes[0].op    = pbs.SET
        attributes[1].name  = pbs.ATTR_NODE_note
        attributes[1].op    = pbs.SET

        batch_list = list()

        ## again a loop, now create the attrib dict list
        for node, note in self._generate_note(nodes, note).items():
            attributes[1].value = note
            batch_list.append(tuple([node, attributes]))

        self._process(batch_list)

    def do_clear(self, nodes):
        '''Clear the state on a node(s) to down, also clear the note'''

        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:do_clear input:%s' % str(nodes), file=sys.stderr)
        attributes          = pbs.new_attropl(2)
        attributes[0].name  = pbs.ATTR_NODE_state
        attributes[0].value = 'down'
        attributes[0].op    = pbs.SET
        attributes[1].name  = pbs.ATTR_NODE_note
        attributes[1].op    = pbs.SET
        attributes[1].value = ''

        batch_list = list()

        ## again a loop, now create the attrib dict list
        for node in nodes:
            batch_list.append(tuple([node, attributes]))

        self._process(batch_list)
  
    def do_modify(self, nodes, note):
        '''Modify the note on a node, override the previous note'''

        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:do_modify input:%s,%s' % (str(nodes), note), file=sys.stderr)
        attributes          = pbs.new_attropl(1)
        attributes[0].name  = pbs.ATTR_NODE_note
        attributes[0].op    = pbs.SET

        batch_list = list()

        ## again a loop, now create the attrib dict list
        for node, note in self._generate_note(nodes, note, append=False).items():
            attributes[0].value = note
            batch_list.append(tuple([node, attributes]))

        self._process(batch_list)

    def do_clear_note(self, nodes):
        '''Clear the  note on the node(s)'''

        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:do_clear_note input:%s' % str(nodes), file=sys.stderr)
        attributes          = pbs.new_attropl(1)
        attributes[0].name  = pbs.ATTR_NODE_note
        attributes[0].op    = pbs.SET
        attributes[0].value = ''

        batch_list = list()

        ## again a loop, now create the attrib dict list
        for node in nodes:
            batch_list.append(tuple([node, attributes]))

        self._process(batch_list)

    def _process(self, batch_list):
        '''This function execute the change to the batch server'''

        if ARGS_VERBOSE: 
            _print('class:SaraNodes func:_process input:%s' % str(batch_list), file=sys.stderr)

        ## Always get the pbs_server name, even in dry-run mode
        pbs_server = pbs.pbs_default()
        if not pbs_server:
            _print('Could not locate a pbs server', file=sys.stderr)
            sys.exit(1)

        if ARGS_VERBOSE:
            _print('class:SaraNodes func:_process pbs_server:%s' % pbs_server, file=sys.stderr)

        ## If dry-run is not specified create a connection
        if not ARGS_DRYRUN:
            pbs_connection = pbs.pbs_connect(pbs_server)

        ## Execute the changes
        for node in batch_list:
            if not ARGS_DRYRUN:
                pbs_connection = pbs.pbs_connect(pbs_server)
                rcode = pbs.pbs_manager(pbs_connection, pbs.MGR_CMD_SET, pbs.MGR_OBJ_NODE, node[0], node[1], 'NULL')
                if rcode > 0:
                    errno, text = pbs.error()
                    _print('PBS error for node \'%s\': %s (%s)' % (node[0], text, errno), file=sys.stderr)
            else:
                _print("pbs.pbs_manager(pbs_connection, pbs.MGR_CMD_SET, pbs.MGR_OBJ_NODE, %s, %s, 'NULL')" % (node[0], str(node[1])))

        ## Close the connection with the batch system
        if not ARGS_DRYRUN:
            pbs.pbs_disconnect(pbs_connection)

if __name__ == '__main__':
    ## The arguments of sara_nodes
    parser = argparse.ArgumentParser(
        description=HELP_DESCRIPTION,
        epilog=HELP_EPILOG,
    )
    parser.add_argument('nodes', metavar='NODES', nargs='*', type=str)
    parser.add_argument('-v','--verbose', action='store_true', help='enables verbose mode')
    parser.add_argument('-n','--dry-run', action='store_true', help='enables dry-run mode')
    parser.add_argument('-q','--quiet', action='store_true', help='enables to supress all feedback')
    parser.add_argument('-o','--offline', metavar='NOTE', help='change state to offline with message')
    parser.add_argument('-m','--modify', metavar='NOTE', help='change the message of a node')
    parser.add_argument('-c','--clear', action='store_true', help='change the state to down')
    parser.add_argument('-N','--clear-note', action='store_true', help='clear the message of a node')
    parser.add_argument('-f','--format', metavar='FORMAT', help='change the output of sara_nodes (see footer of --help)')
    parser.add_argument('-t','--ticket', metavar='TICKET', help='add a ticket number to a node')
    parser.add_argument('--version', action='version', version=pbs.version)

    ## Parse the arguments
    args = parser.parse_args()

    ## The options quiet, verbose and dry-run are processed first
    if args.quiet: 
        ARGS_QUIET = True
    if args.verbose: 
        ARGS_VERBOSE = True
    if args.dry_run: 
        ARGS_DRYRUN = ARGS_VERBOSE = True

    if ARGS_VERBOSE: 
        _print('func:__main__ checking type of operation', file=sys.stderr)

    if args.nodes:
        args.nodes = parse_args(args.nodes)

    ## If offline, modify, clear, clear_note or ticket then initiate the SaraNodes class
    if args.offline or args.modify or args.clear or args.clear_note or args.ticket:
        if not args.nodes:
            _print('You did not specify any nodes, see --help', file=sys.stderr)
            sys.exit(1)

        sn = SaraNodes()
        if args.ticket: 
            sn.ticket = args.ticket 

        if args.offline:
            if ARGS_VERBOSE: 
                _print('func:__main__ call sn.do_offline', file=sys.stderr)
            sn.do_offline(args.nodes, args.offline)
        elif args.modify:
            if ARGS_VERBOSE: 
                _print('func:__main__ call sn.do_modify', file=sys.stderr)
            sn.do_modify(args.nodes, args.modify)
        elif args.clear:
            if ARGS_VERBOSE: 
                _print('func:__main__ call sn.do_clear', file=sys.stderr)
            sn.do_clear(args.nodes)
        elif args.clear_note:
            if ARGS_VERBOSE: 
                _print('func:__main__ call sn.do_clear_note', file=sys.stderr)
            sn.do_clear_note(args.nodes)
        elif args.ticket:
            if ARGS_VERBOSE: 
                _print('func:__main__ call sn.do_modify')
            sn.do_offline(args.nodes, '')
    else:
        if ARGS_DRYRUN:
            _print('Dry-run is not available when we use PBSQuery', file=sys.stderr)

        if args.format:
            if ARGS_VERBOSE: 
                _print('func:__main__ call print_overview_format', file=sys.stderr)
            print_overview_format(args.nodes, args.format)
        else:
            if ARGS_VERBOSE: 
                _print('func:__main__ call print_overview_normal', file=sys.stderr)
            print_overview_normal(args.nodes)
   
    if ARGS_VERBOSE: 
        _print('func:__main__ exit', file=sys.stderr)
