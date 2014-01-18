#!/usr/bin/python
#
import sys
import pbs

def test_init():
  print 'Test init'
  t = pbs.new_attropl(1)
  print type(t)
  print str(t)

  w = pbs.new_attropl(2)
  print type(w)

def test_getitem():
  print 'Test getitem'
  w = pbs.new_attropl(2)
  b = w[0]
  c = w[1]

  b.name = 'bas'
  b.value = 'vlies'
  b.op = pbs.INCR;
  print type(b)
  print 'b', str(b)

  c.name = 'cbassssssssssss'
  c.value = 'cvlies'
  c.op = pbs.DECR 
  print type(c)
  print 'c', str(c), repr(c)

def test_loop():
  print 'Loop'
  w = pbs.new_attropl(2)
  w[0].name = 'bas'
  w[0].value = 'man'

  w[1].name = 'jaap'
  w[1].value = 'man'

  for i in w:
    print i.name


test_init()
test_getitem()
test_loop()

print "Testing"
pbs_server = pbs.pbs_default()
con = pbs.pbs_connect(pbs_server)

z = pbs.new_attropl(2)
z[0].name = pbs.ATTR_u 
z[0].value = 'a403vink,zuidema'
z[0].op = pbs.EQ

z[1].name = pbs.ATTR_N 
z[1].value = 'runRollCV'
z[1].op = pbs.EQ

q = pbs.new_attropl(1)
q[0].name = pbs.ATTR_u 
q[0].value = 'zuidema'
q[0].op = pbs.EQ


combine = z + q
jobs = pbs.pbs_selectjob(con, z, "NULL")

print type(jobs)
for i in jobs:
  print i


#print 'bla'
#print pbs.ptrvalue(jobs,0)
#if pbs.ptrvalue(jobs,0) == 'NULL':
#  print 'yes'
#  sys.exit(1)
#print pbs.ptrvalue(jobs,1)
#print pbs.ptrvalue(jobs,2)
#print pbs.ptrvalue(jobs,3)

