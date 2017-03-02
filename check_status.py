
# Given a list of tasks, produce an html of the status output.

from aux import *
import sys

import time

if len(sys.argv)<3:
    print("Usage: python check_status.py <tasklist> <htmloutput>")
    sys.exit(-1)

fname = sys.argv[1]
htmlout = sys.argv[2]


t0 = time.time()


print("Reading %s..."%fname)
tasks,ignores = read_task_list(fname)
print("... done reading.")


s = ""
s += "<html>\n<body>"
s += "<table>\n"
for task in tasks:
    s += "<tr>"
    s += "<td>%s</td>"%task["command"]
    s += "</tr>\n"

s += "</table>\n"


print("Writing %s..."%htmlout)
f = open(htmlout,'w')
f.write(s)
f.close()
print("...done")


print("This took %f seconds"%(time.time()-t0))


