# Simple task manager

This is quite a simple program, in which you can set a number of tasks on a queue, and when one finishes it will start the next, so that at any time there is a number N of processes running in parallel (and this number can be set by the user).


## Input
As input, this takes a CSV file in which each line contains one task. The format is as follows:
```
wd1,cmd1,result1
wd2,cmd2,result2
...
```
Where `wdX` is the working directory within which the task `X` should be executed, `cmdX` is the command to be executed, and `resultX` is the name of a file that, when it appears, indicates that the task is completed. The `resultX` file is mostly used when we start with a queue on which a number of tasks are already completed; then the program can simply search which files exists and it knows it won't have to run those tasks again.



## TODO
- Allow easy selection between tcsh or other shells.




