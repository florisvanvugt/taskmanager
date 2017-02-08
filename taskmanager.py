
# Basically what I want to do here is have a manager
# that I can let do various tasks (run scripts)
# so that it never exceeds a maximum number of 
# them running simultaneously.

# It also monitors which ones have completed.


# As input we take a list of [scriptcall,result]



import wx



import pandas as pd
import numpy as np
import struct

import os

import subprocess
import time
import datetime

from threading  import Thread
import sys

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

TIMER_INTERVAL = 1000

TIMEFORMAT = "%d %b %H:%M:%S"


LOGDIR = ".logs"



def enqueue_output(out, err, queue):
    """ 
    For reading queued output; source
    http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
    """
    for stream in [out,err]:
        for line in iter(stream.readline, b''):
            queue.put(line)
        stream.close()








class Main(wx.Frame):


  
    def __init__(self, parent, title):
        super(Main, self).__init__(parent, title=title, 
                                   size=(900, 700))

        # This is the timer that keeps updating the processes (checking when processes have completed)
        self.timer = wx.Timer(self)
        
        self.dialog = wx.FileDialog(None, 'Open', wildcard="*", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        self.tasks = []

        self.InitUI()
        self.Show()

        self.n_active = 0
        self.n_processes = None

        self.running = False
        self.processes = []
        self.processes_completed = []


        if not os.path.exists(LOGDIR):
            os.makedirs(LOGDIR)
        

        # If people gave a filename on the command line, open it now
        if len(sys.argv)>1:
            fname = sys.argv[1]
            print("Opening file %s"%fname)
            self.readfile([fname])
    

        




    def ask_path(self):
        # Ask for a file
        if self.dialog.ShowModal() == wx.ID_OK:
            path = self.dialog.GetPaths()
        else:
            path = None
        #dialog.Destroy()
        return path



    def check_status(self,e):
        ## What this function does is, for each of the tasks, check the status, 
        ## and then show that in the GUI.

        for task in self.tasks:
            if task["status"]=="unknown":
                if os.path.exists(task["result"]):
                    task["status"]="completed"
                else:
                    task["status"]="to do"
        
        # Now update what we've found in the GUI
        self.update_status()
        





    def openFile(self,e):
        #participant = "act01"
        #fname = "audiomotor/act01/act01_audiomotor.training_sonif-halfcirc-active-1.0_20160209-120218.trials.txt"
        fnames = self.ask_path()

        data_collection = {}

        # This is a dict that tells us for each trial which filename supplies that trial.
        # If there are multiple files, then there will be multiple entries.
        alltrials = {}

        if fnames==None:
            print("No files selected.")
            #sys.exit(-1)
            return


        self.readfile(fnames)



        
    def readfile(self,fnames):
        """ Read the task list from a file. """
        
        self.filenamet.SetValue("\n".join(fnames))

        participant = None

        for fname in fnames:
            
            self.reportt.AppendText("Reading task list %s\n"%fname)

            ## Read the task list
            self.tasks = []

            f = open(fname,'r')
            lns = f.readlines()
            f.close()

            for l in lns:
                items = [ it.strip() for it in l.split(',') ]
                if len(items)==3:
                    self.tasks.append({"cwd"     :items[0], # the directory where the command should be ran from
                                       "command" :items[1], # the command to be run
                                       "result"  :items[2], # the expected result file (will be used to determine whether we are done)
                                       "status"  :"unknown"})
                
            self.update_status()

        self.check_status(None)
            




    def update_status(self):
        ## Show the status of the tasks
        self.reportt.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        self.reportt.SetValue("")
        if self.running:
            self.reportt.AppendText("--- RUNNING (%i/%i active threads) ---\n\n"%(self.n_active,self.n_processes))
        else:
            self.reportt.AppendText("--- NOT RUNNING ---\n\n")

        for task in self.tasks:
            self.reportt.AppendText("'%s' -> '%s' "%(task["command"],task["result"]))
            if task["status"]=="unknown":
                self.reportt.SetDefaultStyle(wx.TextAttr((100,100,100)))
            if task["status"]=="completed":
                self.reportt.SetDefaultStyle(wx.TextAttr((0,200,0)))
            if task["status"]=="failed":
                self.reportt.SetDefaultStyle(wx.TextAttr(wx.RED))
            if task["status"]=="killed":
                self.reportt.SetDefaultStyle(wx.TextAttr(wx.RED))
            if task["status"]=="to do":
                self.reportt.SetDefaultStyle(wx.TextAttr(wx.BLUE))
            if task["status"]=="running":
                self.reportt.SetDefaultStyle(wx.TextAttr((200,200,0)))

            self.reportt.AppendText("[%s]"%task["status"])
            if task["status"]=="failed":
                self.reportt.AppendText("(exit = %i)"%task["returnval"])
            self.reportt.SetDefaultStyle(wx.TextAttr(wx.BLACK))
            if "started" in task.keys():                
                self.reportt.AppendText(" started %s "%task["started"].strftime(TIMEFORMAT))
            if "finished" in task.keys():
                self.reportt.AppendText(" finished %s "%task["finished"].strftime(TIMEFORMAT))
            self.reportt.AppendText("\n")

        # Now get the whole contents and save them to a log file.
        conts = self.reportt.GetValue()
        f = open(LOGDIR+'/log.txt','w')
        f.write(conts)
        f.close()

        return





    def InitUI(self):
    
        panel = wx.Panel(self)

        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)
        boldfont = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        boldfont.SetPointSize(12)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Tasks file')
        st1.SetFont(font)
        hbox1.Add(st1, flag=wx.RIGHT, border=8)

        self.filenamet = wx.TextCtrl(panel)
        self.filenamet.SetEditable(False)

        hbox1.Add(self.filenamet, proportion=1, flag=wx.EXPAND, border=8)
        self.openb = wx.Button(panel, label='Open', size=(70, 30))
        self.openb.Bind(wx.EVT_BUTTON,self.openFile)

        self.checkb = wx.Button(panel, label='Check status', size=(100, 30))
        self.checkb.Bind(wx.EVT_BUTTON,self.check_status)

        hbox1.Add((10,0))
        hbox1.Add(self.openb,border=8)
        hbox1.Add(self.checkb,border=8)

        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add((10,0))
        st1 = wx.StaticText(panel, label='# parallel processes')
        st1.SetFont(font)
        hbox1.Add(st1, flag=wx.RIGHT, border=8)
        self.parproc = wx.TextCtrl(panel)
        self.parproc.SetValue("3")
        self.parproc.Bind(wx.EVT_TEXT,self.nparprocchanged)
        hbox1.Add(self.parproc)
        vbox.Add(hbox1)




        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Tasks')
        st1.SetFont(font)
        hbox1.Add(st1, flag=wx.RIGHT, border=8)

        self.reportt = wx.TextCtrl(panel,style=wx.TE_MULTILINE,size=(-1,350))
        self.reportt.SetEditable(False)

        hbox1.Add(self.reportt, proportion=1, flag=wx.EXPAND, border=8)

        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM, border=10)



        vbox.Add((-1, 10))


        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Trial')
        st1.SetFont(font)
        self.triallbl = wx.StaticText(panel, label='N/A')
        self.triallbl.SetFont(boldfont)
        hbox2.Add(st1, flag=wx.RIGHT, border=8)
        hbox2.Add(self.triallbl, flag=wx.RIGHT, border=8)
        vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)



        vbox.Add((-1, 10))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add((10,-1))
        self.runb = wx.Button(panel, label='Run', size=(70, 30))
        self.runb.Bind(wx.EVT_BUTTON,self.startrun)
        hbox2.Add(self.runb,border=8)

        self.pokeb = wx.Button(panel, label='Poke', size=(70, 30))
        self.pokeb.Bind(wx.EVT_BUTTON,self.poke)
        hbox2.Add(self.pokeb,border=8)

        self.killb = wx.Button(panel, label='Kill', size=(70, 30))
        self.killb.Bind(wx.EVT_BUTTON,self.killall)
        hbox2.Add(self.killb,border=8)

        vbox.Add(hbox2, border=10)

        vbox.Add((-1, 10))

        panel.SetSizer(vbox)
        self.update_enabled()

        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)






    def read_process_outputs(self,e):
        """
        This goes through all active processes and
        sees if they have output waiting, if so writes
        it to the corresponding log files.
        """

        for proc in self.processes:

            if proc!=None:

                # read line without blocking
                q = proc["queue"]
                keep_reading = True
                while keep_reading:
                    try:  
                        line = q.get_nowait() # or q.get(timeout=.1)
                    except Empty:
                        keep_reading = False
                    else: # got line
                        proc["log"].write(str(line)) # TODO update this
                        # See if we have some more output
                        proc["log"].flush()


                # If the task is no longer running
                if proc["task"]["status"]!="running":
                    proc["log"].close()



    def keep_active(self,e):
        """ 
        This checks if we want to insert a new process (if a slot has opened)
        and then does so.
        """
        self.get_n_processes()
        self.read_process_outputs(e)

        n_active = 0  # how many processes are currently active
        for proc in self.processes:

            if proc!=None and proc["task"]["status"]=="running":
                ret = proc["process"].poll()

                if ret==None:
                    # This means it's still active, still running
                    n_active+=1

                else:
                    # If the process is completed...
                    proc["task"]["returnval"]=ret
                    if ret==0:
                        proc["task"]["status"]="completed"
                    else:
                        proc["task"]["status"]="failed"

                    proc["task"]["finished"]=datetime.datetime.now()
                    proc["log"].write('\nCompleted: %s\n'%(proc["task"]["finished"].strftime(TIMEFORMAT)))
                    proc["log"].flush()


        if n_active<self.n_processes: # If we have less active processes than the maximum, we can 

            # Find if we have a task that needs to be assigned to a processes
            newlaunched = False
            for task in self.tasks:
                if task["status"]=="to do":

                    spltask = task["command"].split(" ")
                    if len(spltask)>1:
                        cmd = spltask
                    else:
                        cmd = ["tcsh",task["command"]] #.split(" ")
                    print("Launching '%s'"%task["command"])
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX, cwd=task["cwd"])

                    # Create a queue+thread for reading out the STDOUT/STDERR pipelines associated with this process
                    q = Queue()
                    t = Thread(target=enqueue_output, 
                               args=(p.stdout, p.stderr, q))
                    t.daemon = True # thread dies with the program
                    t.start()

                    fnamesafe = task["command"].replace(" ","")
                    fnamesafe = fnamesafe.replace("/","")
                    f = open(LOGDIR+'/log%s.txt'%fnamesafe,'w')
                    f.write('Log for running "%s"\n'%fnamesafe)
                    task["started"]=datetime.datetime.now()
                    f.write('Started running: %s\n\n'%task["started"].strftime(TIMEFORMAT))
                    f.flush()

                    self.processes.append({"task"    :task,
                                           "process" :p,  # The process variable
                                           "queue"   :q,  # Queue is used for reading output from stderr and stdout
                                           "thread"  :t,
                                           "log"     :f})
                    task["status"]="running"
                    newlaunched = True
                    break

            if n_active==0 and not newlaunched:

                print("All processes completed.")
                self.running = False
                self.timer.Stop()
                self.update_status()

        self.n_active=n_active



    def get_n_processes(self):
        try:
            self.n_processes = int(self.parproc.GetValue().strip())
        except:
            msg = "Invalid # of parallel processes (%s). This must be an integer."%self.parproc.GetValue()
            print(msg)
            wx.MessageBox(msg,"Information",
                          wx.OK | wx.ICON_INFORMATION)





    def startrun(self,e):

        self.get_n_processes()
        if self.n_processes == None:
            print ("No processes.")
            return


        if self.running:
            msg = "Already running!"
            print(msg)
            wx.MessageBox(msg,"Information",
                          wx.OK | wx.ICON_INFORMATION)
            return

        if len(self.tasks)==0:
            msg = "No tasks to do!"
            print(msg)
            wx.MessageBox(msg,"Information",
                          wx.OK | wx.ICON_INFORMATION)
            return


        self.check_status(e)
        self.running = True

        # Let's go!
        self.processes = [] # None for _ in range(self.n_processes) ]

        self.timer.Start(TIMER_INTERVAL)

        print ("Starting!")



    def poke(self,e):
        if self.running:
            self.keep_active(e)
        self.update_status()



    def killall(self,e):
        if not self.running:
            msg = "Not running anything."
            print(msg)
            wx.MessageBox(msg,"Information",
                          wx.OK | wx.ICON_INFORMATION)
            return

        # Terminate all processes
        for proc in self.processes:
            if proc!=None:
                proc["process"].terminate()
                proc["task"]["status"]="killed"
        self.running = False
        self.update_status()
        self.timer.Stop()



    def update_enabled(self):
        pass

    def textchanged(self,e):
        self.update_enabled()


    def OnCloseWindow(self, e):
        self.Close()


    def nparprocchanged(self,e):
        self.get_n_processes()


    def on_timer(self,e):
        if not self.running:
            self.timer.Stop()

        else:
            self.keep_active(e)
        self.update_status()





if __name__ == '__main__':

    app = wx.App()
    n = Main(None, title='Parallel Script Running Manager')
    n.__close_callback = lambda: True
    app.MainLoop()


