#!/usr/bin/python

import sys
import pbs

def test_init():
  print 'Test init'

  w = pbs.new_attrl(2)
  print type(w)

  print 'end Test init'

def test_getitem():
  print 'Test getitem'

  w = pbs.new_attrl(2)
  b = w[0]
  c = w[1]

  print b, type(b)

  b.name = 'bas'
  b.value = 'vlies'
  print 'b', b

  c.name = 'cbassssssssssss'
  c.value = 'cvlies'
  print 'c', c

def test_loop():
  print 'Test loop'
  w = pbs.new_attrl(2)
  b = w[0]
  c = w[1]

  b.name = 'bas'
  b.value = 'vlies'
  c.name = 'jaap'
  c.value = 'dijkshoorn'

  for i in w:
    print i


test_init()
test_getitem()
test_loop()

pbs_server = pbs.pbs_default()
con = pbs.pbs_connect(pbs_server)
print con

z = pbs.new_attrl(2)
z[0].name = 'state'
z[1].name = 'ntype'

#z.append('bla');
#print 'z', z

for entry in z:
  print 'entry', entry

x = pbs.new_attrl(1)
x[0].name = 'np'

combine = z + x
print combine, len(combine)

#print combine[0].name
#print combine[1].name
#print combine[2].name

nodes = pbs.pbs_statnode(con, "", 'NULL', "NULL")
for node in nodes:
  print node.name, ':'
  for prop in node.attribs:
     print '\t', prop.name, ' = ',  prop.value

queues = pbs.pbs_statque(con, "", 'NULL', "")
for queue in queues:
  print queue.name
  for attrib in queue.attribs:
    print '\t', attrib.name, ' = ',  attrib.value

jobs = pbs.pbs_statjob(con, "", 'NULL', "")
for job in jobs:
  print job.name
  for attrib in job.attribs:
    print '\t', attrib.name, ' = ',  attrib.value

sys.exit(0)

## OLD stuff obselete
##
while batch_info.this:
  node_attr = batch_info.attribs
  print batch_info.name, ':'
  while node_attr.this:
    # print node_attr.this
    print '\t', node_attr.name ,node_attr.value
    node_attr = node_attr.next

  batch_info =  batch_info.next

