

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
