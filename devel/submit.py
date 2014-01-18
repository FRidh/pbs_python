import pbs

pbs_server = pbs.pbs_default ()
pbsconn = pbs.pbs_connect (pbs_server)

print pbsconn

attrl = pbs.new_attropl(1)
attrl[0].name = pbs.ATTR_N
attrl[0].value = "test"

task_id = pbs.pbs_submit(pbsconn, attrl, "A1.tsk", 'NULL', 'NULL')

e, e_txt = pbs.error()
if e:
	print e,e_txt

print task_id
