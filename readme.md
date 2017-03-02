# Simple task manager

This is quite a simple program designed to handle running exorbitant numbers of scripts, not all at the same time in parallel, but with a user-specified maximum number that should be running at any one time. You feed this program a task list file (see details below) of scripts, which it will execute in order, and when one finishes it will start the next, so that at any time there is a number N of processes running in parallel (and this number can be set by the user).


## Graphical

There is a graphical user interface version, which requires wxPython, which you can run by typing:

```
python taskmanager.py
```

## Command-line

There is also a command line version, which you can run as follows:

```
python autospawn.py <tasklist> <n_processes> <html-output>
```

This will read the task list file (for details about its format see below), and start running them in parallel but at most `<n_processes>` at any one time. It will keep an output file `<html-output>` which gets updated every now and then. Once you launch with the above command, you can open the HTML file you specified in the browser and see an overview of which scripts are running, or completed.

## Task list file
As input, this takes a CSV file in which each line contains one task. The format is as follows:

```
wd1,cmd1,result1
wd2,cmd2,result2
...
```

Where `wdX` is the working directory within which the task `X` should be executed, `cmdX` is the command to be executed, and `resultX` is the name of a file that, when it appears, indicates that the task is completed. The `resultX` is an indicator file, which is essentially a file that you know will be created when the task is done. The purpose of this is that it allows you to have large task list, some of which might already be done when you start the task manager, and then the task manager will figure out by itself which scripts it still needs to run and which are already done previously.



