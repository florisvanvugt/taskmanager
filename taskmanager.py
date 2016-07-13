
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

TIMER_INTERVAL = 1000

TIMEFORMAT = "%d %b %H:%M:%S"

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

        self.running = False
        self.processes = []
        self.processes_completed = []
        





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
                if len(items)==2:
                    self.tasks.append({"command":items[0],
                                       "result": items[1],
                                       "status": "unknown"})
                
            self.update_status()





    def update_status(self):
        ## Show the status of the tasks
        self.reportt.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        self.reportt.SetValue("")
        if self.running:
            self.reportt.AppendText("--- RUNNING ---\n\n")
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
            self.reportt.SetDefaultStyle(wx.TextAttr(wx.BLACK))
            if "started" in task.keys():                
                self.reportt.AppendText(" started %s "%task["started"].strftime(TIMEFORMAT))
            if "finished" in task.keys():
                self.reportt.AppendText(" finished %s "%task["finished"].strftime(TIMEFORMAT))
            self.reportt.AppendText("\n")

        return





    def InitUI(self):
    
        panel = wx.Panel(self)

        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)
        boldfont = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
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






    def keep_active(self,e):
        """ 
        This checks if we want to insert a new process (if a slot has opened)
        and then does so.
        """
        for i in range(self.n_processes):
            # If the i-th process slot is currently idle
            if self.processes[i]!=None:
                ret = self.processes[i]["process"].poll()

                if ret==None:
                    # If it's an on-going process, see if we can read some of its standard output
                    line = None
                    while line!=None:
                        line = proc.stdout.readline()
                        if line != '':
                            self.processes[i]["log"].write(line)

                    # See if we have some more output
                    self.processes[i]["log"].flush()
                    
                else: # None means it's still working

                    # If it's completed...
                    if ret==0:
                        self.processes[i]["task"]["status"]="completed"
                    if ret==-1:
                        self.processes[i]["task"]["status"]="failed"
                    self.processes[i]["task"]["finished"]=datetime.datetime.now()
                    self.processes[i]["log"].write('Completed: "%s"\n\n'%(self.processes[i]["task"]["finished"].strftime(TIMEFORMAT)))
                    self.processes[i]["log"].close()
                    self.processes_completed.append(self.processes[i])
                    self.processes[i]=None


            if self.processes[i]==None:

                # Find if we have a task that needs to be assigned to a processes
                assigned = False
                for task in self.tasks:
                    if (not assigned) and task["status"]=="to do":

                        cmd = task["command"].split(" ")
                        print("Launching '%s'"%task["command"])
                        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                        
                        fnamesafe = task["command"].replace(" ","")
                        fnamesafe = fnamesafe.replace("/","")
                        f = open('log%s.txt'%fnamesafe,'w')
                        f.write('Log for running "%s"\n'%fnamesafe)
                        task["started"]=datetime.datetime.now()
                        f.write('Started running: "%s"\n\n'%task["started"].strftime(TIMEFORMAT))

                        self.processes[i]={"task"    :task,
                                           "process" :p,
                                           "log"     :f}
                        task["status"]="running"
                        assigned = True # we've assigned this process slot, let's go on

                if not assigned:
                    # We haven't found another task to do, so no need to keep trying!
                    pass
                

        still_running = False
        for i in range(self.n_processes):
            if self.processes[i]!=None:
                still_running=True

        if not still_running:
            print("All processes completed.")
            self.running = False
            self.timer.Stop()






    def startrun(self,e):
        try:
            self.n_processes = int(self.parproc.GetValue().strip())
        except:
            msg = "Invalid # of parallel processes (%s). This must be an integer."%self.parproc.GetValue()
            print(msg)
            wx.MessageBox(msg,"Information",
                          wx.OK | wx.ICON_INFORMATION)
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
            
        self.running = True

        # Let's go!
        self.processes = [ None for _ in range(self.n_processes) ]
        self.processes_completed = []

        self.timer.Start(TIMER_INTERVAL)



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


    def on_timer(self,e):
        if not self.running:
            self.timer.Stop()

        else:
            self.keep_active(e)
        self.update_status()





if __name__ == '__main__':
  
    app = wx.App()
    n = Main(None, title='Trajectory Replay Generator')
    n.__close_callback = lambda: True
    app.MainLoop()


