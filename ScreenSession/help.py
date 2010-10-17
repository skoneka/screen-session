#!/usr/bin/env python

help="Usage: screen-session [mode] [options]\n\
Help: screen-session [mode] --help\n\
    \n\
Available modes:\n\
    save\t- save sessions to disk\n\
    load\t- load session from savefile\n\
    ls\t\t- list saved sessions\n\
    \n\
    manager\t- sessions manager with split screen preview\n\
    dir\t\t- start Screen window in the same working directory\n\
    regions\t- display number in each region (like tmux display-panes)\n\
    kill\t- send signal to last process started in a window\n\
    kill-zombie\t- kill all zombie windows in session\n\
    grab\t- grab a process and attach it to current tty\n\
    renumber\t- renumber windows to fill gaps\n\
    sort\t- sort windows by title\n\
    "

help_regions="Display number in each region\n\
script reassembling the functionality of tmux display-panes\n\
\nUsage: screen-session regions"

help_kill="Kill last process started in a window\n\
\nUsage: screen-session kill [signal=TERM] [window=current]"

help_kill_zombie="Kill all zombie windows in session\n\
\nUsage: screen-session kill-zombie [maxwin=MAXWIN] [minwin=0]"

help_dir="Start a new Screen window in the same working directory\n\
on the position next to the current window\n\
\nUsage: screen-session dir [program]"

help_grab="Grab a process and attach to the current tty.\n\
Works with applications without complicated output scheme\n\
\nUsage: screen-session grab [PID]\n\
on the previous shell type: $ disown"

help_manage="Sessions manager for GNU Screen with preview in a split window\n\
\nUsage: screen-session manage"

help_renumber="Renumber windows to fill the gaps\n\
\nUsage: screen-session renumber [maxwin=MAXWIN] [minwin=0]"

help_sort="Sort windows by titles\n\
\nUsage: screen-session sort [maxwin=MAXWIN] [minwin=0]"

if __name__=='__main__':
    import sys
    try:
        mode=sys.argv[1]
    except:
        mode='help'
    if mode=='help':
        print(help)
    elif mode=='regions':
        print(help_regions)
    elif mode=='kill':
        print(help_kill)
    elif mode=='kill-zombie':
        print(help_kill_zombie)
    elif mode=='dir':
        print(help_dir)
    elif mode=='grab':
        print(help_grab)
    elif mode=='manage':
        print(help_manage)
    elif mode=='renumber':
        print(help_renumber)
    elif mode=='sort':
        print(help_sort)

