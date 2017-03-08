import os


def read_task_list(fname):
    """ 
    Read the list of tasks from a file, and
    return a list of dicts where each represents basic
    information about a task.
    """
    tasks = []
    ignores = []
    
    f = open(fname,'r')
    lns = f.readlines()
    f.close()
    
    for l in lns:
        items = [ it.strip() for it in l.split(',') ]
        if len(items)==3:
            tasks.append({"cwd"     :items[0], # the directory where the command should be ran from
                          "command" :items[1], # the command to be run
                          "result"  :items[2], # the expected result file (will be used to determine whether we are done)
                          "status"  :"unknown"})
        else:
            if len(l.strip())>0:
                ignores.append("Ignoring line '%s' in task file, not sure what to do with that."%(l.strip()))

    return tasks,ignores






def check_indicator_files(tasks):
    """ Given a set of tasks, check their indicator files.
    If for a task the status is unknown, go looking for
    the indicator file and put the status to "completed" 
    if the indicator file is present."""

    for task in tasks:
        if task["status"]=="unknown":
            if os.path.exists(task["result"]):
                task["status"]="previously completed"
            else:
                task["status"]="to do"
    return




# The colours we will display each of the task statuses in
status_colors = {
    "unknown"               : "gray",
    "failed"                : "red",
    "running"               : "blue",
    "todo"                  : "gray",
    "completed"             : "#008000",
    "previously completed"  : "#007200"
    }


status_order = ["unknown","previously completed","completed","failed","running","to do"]



def tasks_to_html_table(tasks):
    """
    Returns an HTML table containing all the tasks (completed, running and todo).
    """
    s = ""
    s += "<table>\n"
    status_seen = []
    for i,task in enumerate(tasks):
        s += "<tr><td>"

        if task["status"] not in status_seen:
            status_seen.append(task["status"])
            s += "<a name=\"%s\"></a>"%(task["status"])
        
        s += "%i.</td>"%(i+1)
        s += "<td>%s</td>"%task["command"]
        stl = "color:%s"%status_colors.get(task["status"],"gray")
        details = ""
        if task["status"]=="running":
            if "started" in list(task.keys()):
                details = " [started %s]"%task["started"]
            
        if task["status"]=="completed" or task["status"]=="previously completed":
            if "finished" in list(task.keys()):
                details = " [%s]"%task["finished"]
        s += "<td style=\"%s\">%s %s</td>"%(stl,task["status"],details)
        if "logfname" in list(task.keys()):
            s += "<td><a href=\"%s\">log</a></td>"%task["logfname"]
        s += "</tr>\n"

    s += "</table>\n"
    return s




def tasks_to_html(tasks,header="",logf=""):
    """ Given a list of tasks, produce a HTML summary of where each task is at. """
    s = ""
    s += "<html>\n<body>"
    s += "<p>%s</p>\n"%header
    s += '<p><a href="javascript:window.location.reload(true)">Reload</a></p>\n'
    if logf!="":
        s += '<p><a href="%s">Log</a></p>\n'%logf
    s += tasks_to_html_table(tasks)
    return s
