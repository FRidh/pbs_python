#!/usr/bin/python

import sys
import pbs

pbs_server = pbs.pbs_default()
con = pbs.pbs_connect(pbs_server)

print con

z = pbs.new_attrl(1) 
z[0].name = 'state'
print z[0].name

batch_info = pbs.pbs_statnode(con, "", z, "NULL")
#print type(batch_info), batch_info, batch_info.name
print type(batch_info), batch_info
print 'bas'
print type(batch_info[0])
print batch_info[0]
print batch_info[0].name

#b = pbs.batch_statusPtr(batch_info[0])
#print type(b)
#print b
#print b.name
#sys.exit(1)

while batch_info.this:
  node_attr = batch_info.attribs
  print batch_info.name, ':'
  while node_attr.this:
    # print node_attr.this
    print '\t', node_attr.name ,node_attr.value
    node_attr = node_attr.next

  batch_info =  batch_info.next
