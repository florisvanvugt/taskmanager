
from aux import *
import subprocess
import time
import datetime

import sys

import time

import shlex

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


TSTAMP_FSAFE = "%Y%m%d_%H%M%S" # a timestamp format that is safe for appending to a file
timestmp = datetime.datetime.now().strftime(TSTAMP_FSAFE)
LOGFNAME = "%s/log_%s.txt"%(LOGDIR,timestmp)
LOGF = open(LOGFNAME,'w')


started = datetime.datetime.now()







def nowiswhat():
    """ The current time in readable format. """
    return datetime.datetime.now().strftime(TIMEFORMAT)
    


# The total width (in pixels) of the bar where we show for each type of task, how many there are in total
BAR_WIDTH  = 500
BAR_HEIGHT = 25





def intermediate_report(tasks,nproc=None):
    """ Make an intermediate report: where are we at now? """

    statuses = {}
    for task in tasks:
        statuses[task["status"]]=statuses.get(task["status"],0)+1
    summ = "%s (started %s) --- Tasks : "%(nowiswhat(),started) + " / ".join([ "<span style=\"font-weight:bold\">%i</span> %s"%(statuses[st],st) for st in statuses.keys() ])
    summ += "; total %i"%(len(tasks))
    
    html = ""
    html += "<html>\n<body>\n\n"
    html += "<table><tr><td>Current time</td><td>%s</td></tr>\n"%nowiswhat()
    html += "<tr><td>Started</td><td>%s</td></tr>\n"%(started.strftime(TIMEFORMAT))

    running_time = time.time() - time.mktime(started.timetuple())
    html += "<tr><td>Running time</td><td>%.03f hours</td></tr>\n"%(running_time/3600.)
    if nproc!=None:
        html += "<tr><td>N. parallel processes</td><td>%i</td></tr>\n"%(nproc)

    # If you can, make a prediction about how long it will take
    n_completed = statuses.get('completed',0)
    if n_completed:

        # Approximately; because we run multiple tasks at the same time
        timepertask = running_time/n_completed

        if timepertask>0:
            # Time left: time to do
            timeleft = statuses.get("to do",0)*timepertask
            html += "<tr><td>Estimated time left</td><td>%.03f hours (for remaining to-do tasks)</td></tr>\n"%(timeleft/3600.)
        
    
    html += "</table>\n"

    # Make an overview of how many tasks are completed, running, etc.
    statuses = {}
    for task in tasks:
        statuses[task["status"]]=statuses.get(task["status"],0)+1
    status_display = [ s for s in status_order if s in list(statuses.keys()) ] # in order of display
        
    html += "<p>\n"
    for st in status_display:
        col = status_colors.get(st,"gray")
        w = int((statuses[st]/float(len(tasks)))*BAR_WIDTH)
        html += "<span style=\"display:block;background:%s;color:%s;width:%ipx;height:%ipx;float:left\"></span>\n"%(col,col,w,BAR_HEIGHT)
    html += "<span style=\"display:block;width:30px;height:%ipx;float:left\"></span>\n\n"%BAR_HEIGHT
        
    html += " / ".join([ "<a href=\"#%s\" style=\"text-decoration: none\"><span style=\"color:%s\"><span style=\"font-weight:bold\">%i</span> %s</span></a>"%(st,status_colors.get(st,"gray"),statuses[st],st) for st in status_display ])
    html += "</p>"
    
    # Now let's make a fancy bar plot-style representation
    
    html += '<p><a href="javascript:window.location.reload(true)">Reload</a></p>\n'
    html += '<p><a href="%s">Taskmanager log</a></p>\n\n'%LOGFNAME
    html += tasks_to_html_table(tasks)
    html += "</body></html>\n"

    outp = open(htmlout,'w')
    outp.write(html)
    outp.close()

    summ = "%s (started %s) --- Tasks : "%(nowiswhat(),started) + " / ".join([ "%i %s"%(statuses[st],st) for st in statuses.keys() ])
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
        return intermediate_report(self.tasks,self.n_processes)
        
    
    def keep_active(self):
        """ 
        This checks if we want to insert a new process (if a slot has opened)
        and then does so.
        """

        n_active = 0  # how many processes are currently known to be active
        tasks_changed = False # whether something has changed (so that we should generate a new report)
        newlaunched = False # whether we launched any new task
        
        for proc in self.processes:

            if proc!=None and proc["task"]["status"]=="running":
                ret = proc["process"].poll()

                if ret==None:
                    # This means it's still active, still running
                    n_active+=1

                else:
                    # If the process is completed...
                    proc["task"]["returnval"]=ret
                    self.log_entry("Ended task '%s'; return value %i"%(proc["task"]["command"],proc["task"]["returnval"]))
                    if ret==0:
                        proc["task"]["status"]="completed"
                    else:
                        proc["task"]["status"]="failed"

                    proc["task"]["finished"]=datetime.datetime.now().strftime(TIMEFORMAT)
                    proc["log"].write('\n## Ended: %s\n'%(proc["task"]["finished"]))
                    #proc["log"].flush()
                    proc["log"].close()

                    tasks_changed = True
                    

        if n_active<self.n_processes: # If we have less active processes than the maximum, we can add some new

            #self.log_entry("Currently %i processes active, which is less than the desired %i"%(n_active,self.n_processes))

            # Find if we have a task that needs to be assigned to a processes
            for task in self.tasks:
                if task["status"]=="to do":

                    spltask = shlex.split(task["command"])
                    if len(spltask)>1:
                        cmd = spltask
                    else:
                        cmd = ["tcsh",task["command"]] #.split(" ")

                    # Create a log file that we will capture any output in.
                    fnamesafe = task["command"].replace(" ","")
                    fnamesafe = fnamesafe.replace("/","")
                    tstmp = datetime.datetime.now().strftime(TSTAMP_FSAFE)
                    #proclog = LOGDIR+'/%s_%s.txt'%(tstmp,fnamesafe)
                    proclog = LOGDIR+'/%s_%i.txt'%(tstmp,self.tasks.index(task)+1)
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

                self.log_entry("All processes ended.")
                self.running = False


                
        if tasks_changed or newlaunched:
            # We have launched a new process, so it's time to update the status again!
            msg = self.update_status()
            self.log_entry(msg)

                

                
        self.n_active=n_active















    


log_entry("Started text-based task manager")


log_entry("Reading %s..."%fname)
tasks,ignores = read_task_list(fname)



log_entry("Checking status using indicator files...")
check_indicator_files(tasks)




proc = Processes()
proc.start(tasks)

while proc.running:
    proc.keep_active()
    time.sleep(POLL_INTERVAL)



