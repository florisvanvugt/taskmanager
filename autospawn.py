
from aux import *
import subprocess
import time
import datetime

import sys

import time

if len(sys.argv)<4:
    print("Usage: python autospawn.py <tasklist> <n-processes> <htmloutput>")
    print("")
    print("<tasklist> is a file where each line contains the working directory, script command, and completion indicator file (separated by commas)")
    print("<n-processes> is how many processes you would like to be open at any one time")
    print("<htmloutput> is the name of an HTML output file where you can keep track of the progress")
    sys.exit(-1)

fname = sys.argv[1]
try:
    nproc = int(sys.argv[2])
except:
    print("Number of processes has to be an integer but '%s' found."%sys.argv[2])
    sys.exit(-1)
htmlout = sys.argv[3]




# How long to wait before checking again which tasks have finished
POLL_INTERVAL = 1.0


TIMEFORMAT = "%d %b %H:%M:%S"


LOGDIR = "logs"
if not os.path.exists(LOGDIR):
    os.makedirs(LOGDIR)


timestmp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOGFNAME = "%s/log_%s.txt"%(LOGDIR,timestmp)
LOGF = open(LOGFNAME,'w')





def nowiswhat():
    """ The current time in readable format. """
    return datetime.datetime.now().strftime(TIMEFORMAT)
    


def intermediate_report(tasks):
    """ Make an intermediate report: where are we at now? """

    statuses = {}
    for task in tasks:
        statuses[task["status"]]=statuses.get(task["status"],0)+1
    summ = nowiswhat()+" -- Tasks : " + " / ".join([ "<span style=\"font-weight:bold\">%i</span> %s"%(statuses[st],st) for st in statuses.keys() ])
    summ += "; total %i"%(len(tasks))
   
    html = tasks_to_html(tasks,summ,LOGFNAME)

    outp = open(htmlout,'w')
    outp.write(html)
    outp.close()

    return summ

    


def log_entry(message):
    """ Add an entry to our log. """
    t = time.time()
    t_fmt = datetime.datetime.now().strftime("%a %d %b %Y %H:%M:%S")
    if message[-1]!="\n": # if we aren't already ending in a newline, add one now
        message+="\n"
    msg_string = "[%f] %s -- %s"%(t,t_fmt,message)
    LOGF.write(msg_string)
    print(msg_string.strip())
    LOGF.flush()
    




class Processes:
    

    def start(self,tasks):
        self.tasks = tasks
        self.running = True
        self.log_entry = log_entry
        self.n_processes = nproc

        # Let's go!
        self.processes = [] # None for _ in range(self.n_processes) ]

        self.log_entry("Starting task list of %i tasks."%(len(self.tasks)))




    def update_status(self):
        intermediate_report(self.tasks)
        
    
    def keep_active(self):
        """ 
        This checks if we want to insert a new process (if a slot has opened)
        and then does so.
        """

        n_active = 0  # how many processes are currently known to be active
        for proc in self.processes:

            if proc!=None and proc["task"]["status"]=="running":
                ret = proc["process"].poll()

                if ret==None:
                    # This means it's still active, still running
                    n_active+=1

                else:
                    # If the process is completed...
                    proc["task"]["returnval"]=ret
                    self.log_entry("Completed task '%s'; return value %i"%(proc["task"]["command"],proc["task"]["returnval"]))
                    if ret==0:
                        proc["task"]["status"]="completed"
                    else:
                        proc["task"]["status"]="failed"

                    proc["task"]["finished"]=datetime.datetime.now().strftime(TIMEFORMAT)
                    proc["log"].write('\n## Completed: %s\n'%(proc["task"]["finished"]))
                    #proc["log"].flush()
                    proc["log"].close()


        if n_active<self.n_processes: # If we have less active processes than the maximum, we can add some new

            msg = intermediate_report(self.tasks)
            self.log_entry(msg)
            self.log_entry("Currently %i processes active, which is less than the desired %i"%(n_active,self.n_processes))

            # Find if we have a task that needs to be assigned to a processes
            newlaunched = False
            for task in self.tasks:
                if task["status"]=="to do":

                    spltask = task["command"].split(" ")
                    if len(spltask)>1:
                        cmd = spltask
                    else:
                        cmd = ["tcsh",task["command"]] #.split(" ")


                    # Create a log file that we will capture any output in.
                    fnamesafe = task["command"].replace(" ","")
                    fnamesafe = fnamesafe.replace("/","")
                    proclog = LOGDIR+'/log%s.txt'%fnamesafe
                    f = open(proclog,'w')
                    task["logfname"]=proclog
                    f.write('## Log for running "%s"\n'%str(task["command"]))
                    f.write('## Actual subprocess.Popen() entry: "%s"\n'%(str(cmd)))
                    f.write("## Working directory \"%s\"\n"%(task["cwd"]))
                    task["started"]=datetime.datetime.now().strftime(TIMEFORMAT)
                    f.write('## Started running: %s\n\n'%task["started"])
                    f.flush()

                    p = subprocess.Popen(cmd,
                                         stdout=f,
                                         stderr=f,
                                         #bufsize=1,
                                         #close_fds=ON_POSIX,
                                         cwd=task["cwd"]
                    )

                    self.log_entry("Launching '%s' in directory '%s' (PID %s)"%(task["command"],task["cwd"],str(p.pid)))
                    # Create a queue+thread for reading out the STDOUT/STDERR pipelines associated with this process

                    #q = Queue()
                    #t = Thread(target=enqueue_output, 
                    #           args=(p.stdout, p.stderr, q))
                    #t.daemon = True # thread dies with the program
                    #t.start()


                    self.processes.append({"task"    :task,
                                           "process" :p,  # The process variable
                                           #"queue"   :q,  # Queue is used for reading output from stderr and stdout
                                           #"thread"  :t,
                                           "log"     :f})
                    task["status"]="running"
                    newlaunched = True
                    break

            if n_active==0 and not newlaunched:

                self.log_entry("All processes completed.")
                self.running = False
                self.update_status()

        self.n_active=n_active















    


log_entry("Started text-based task manager")


print("Reading %s..."%fname)
tasks,ignores = read_task_list(fname)
print("... done reading.")



print ("Checking status using indicator files...")
check_indicator_files(tasks)
print ("...done")




proc = Processes()
proc.start(tasks)

while proc.running:
    proc.keep_active()
    time.sleep(POLL_INTERVAL)



