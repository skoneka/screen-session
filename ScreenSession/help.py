#!/usr/bin/env python

VERSION='git'
version_str="SCREEN-SESSION (%s) - a collection of tools for GNU Screen."%VERSION


help_help="\
Usage:\t screen-session [mode] [options]\n\
\t scs [mode] -S session [options]\n\
Help:\t scs [mode] --help\n\
Global Options:\n\
    -S [target]\t- target Screen session\n\
    -W\t\t- wait for keypress\n\
    -h --help\t- display mode help\n\
Saver modes:\n\
    save\t- save session to disk\n\
    load\t- load session from file\n\
    ls\t\t- list saved sessions\n\
Other tools:\n\
    dir\t\t- start Screen window in the same working directory\n\
    dump\t- dump informations about windows in session\n\
    find-pid\t- find PIDs in windows\n\
    find-file\t- find files in windows\n\
    group\t- move windows to a group\n\
    kill\t- send signal to last process started in a window\n\
    kill-group\t- kill a group and all windows inside\n\
    kill-zombie\t- kill all zombie windows in session\n\
    manager\t- sessions manager with split screen preview\n\
    name\t- get or set sessionname\n\
    nest\t- nest layout in the current region\n\
    regions\t- display number in each region (tmux display-panes)\n\
    renumber\t- renumber windows to fill gaps\n\
Report bugs to http://github.com/skoneka/screen-session/issues\
    "
'''
broken/unfinished:
    grab\t- grab a process and attach it to current tty\n\
    \t\t  (requires injcode)\n\
    sort\t- sort windows by title\n\
    manager-remote - 
'''

help_regions="Usage: screen-session regions [options]\n\n\
Display number in each region.\n\
Reassembles the functionality of tmux display-panes.\
"

help_kill="Usage: screen-session kill [options] [signal=TERM] [window=current]\n\n\
Kill last process started in a window.\n\
Useful for closing random emacs/vim instances.\
"

help_kill_zombie="Usage: screen-session kill-zombie [options]\n\
       screen-session kz [options]\n\n\
Kill all zombie windows in session.\
"

help_kill_group="Usage: screen-session kill-group [options] [groupNum0] [groupNum..]\n\
       screen-session kg [options] [groupNum0] [groupNum..]\n\n\
Recursively kill groups and windows inside.\n\
Accepts group window numbers as arguments.\n\
If the first argument is \"current\" kill the current group.\n\
If the first argument is \"all\" kill all groups in session.\n\
Take extra care with this command.\
"

help_dir="Usage: screen-session dir [options] [program]\n\n\
Start a new Screen window in the same working directory\n\
on the position next to the current window.\
"

help_dump="Usage: screen-session dump [options]\n\n\
Dump informations about windows in session.\n\
-P \t- do not show pid data\
"

help_find_pid="Usage: screen-session find-pid [options] [PIDs]\n\
       screen-session fp [options] [PIDs]\n\n\
Example: screen-session find-pid $(pgrep vim)\n\n\
Find PIDs in windows.\
"

help_find_file="Usage: screen-session find-file [options] [files]\n\
       screen-session ff [options] [files]\n\n\
Find files in windows. Requires lsof.\
"

help_grab="Grab a process and attach to the current tty.\n\
Works with applications without complicated output scheme.\n\
A simple demonstration of injcode tool by Thomas Habets.\n\
http://blog.habets.pp.se/2009/03/Moving-a-process-to-another-terminal\n\
\nUsage: screen-session grab [PID]\n\
and on the previous shell type:\n\
$ disown\n\
It works more reliably if commands from the script are typed manually."

help_group="Usage: screen-session group [options] [GROUP] [windows]\n\n\
Move windows to a group.\n\
If no windows given, move the current window.\
"

help_manager="Usage: screen-session manager [account@host]\n\n\
Sessions manager for GNU Screen with preview in a split window.\n\
Requires python 2.5+\
"

help_manager_remote="Usage: screen-session manager-remote\n\n\
Sessions manager for GNU Screen with preview in a split window and support for multiple hosts.\n\
Requires python 2.5+\
"

help_nest="Usage: screen-session nest [options] [TARGET_LAYOUT]\n\n\
Nest layout in the current region.\
"

help_renumber="Usage: screen-session renumber [options]\n\n\
Renumber windows to fill the gaps.\
"

help_sort="Usage: screen-session sort [options]\n\n\
Sort windows by titles.\
"

help_name="Usage: screen-session name [options] [new_sessionname]\n\n\Try to get the current sessionname.\
"

help_saver_modes='GNU Screen session saver.\n\
Usage: screen-session [save|load|ls] [options]'

help_saver_ls="Usage: scs save [options]\n\n\
List saved sesssions.\n\n\
Options:\n\
-i --in     <string>\n\
  \tfilter listed savefiles by <string>\n\
--log       <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\
"

help_saver_save="Usage: scs save [options]\n\n\
Save GNU Screen and VIM sessions to a file.\n\n\
Options:\n\
-i --in  <sesionnname>\n\
  \tspecify target Screen session (by default current session)\n\
-o --out  <savefile>\n\
  \tspecify target filename (by default Screen's session name)\n\
-f --force\n\
  \tforce saving even if savefile with the same name already exists\n\
-e --exclude  <windows>\n\
  \ta comma separated list of windows to be ignored during saving,\n\
  \tif a window is a group all subwindows are also ignored\n\
-H --no-scroll  <windows>\n\
    a comma separeted list of windows which will not save scrollbacks,\n\
    using keyword \"all\" affects all windows\n\
-y --no-layout\n\
  \tdisable layout saving\n\
-V --no-vim\n\
  \tdisable vim session saving\n\
--idle  <seconds>\n\
  \tstart command after <seconds> of inactivity\n\
--log <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
\n\
Example:\n\
$ screen-session save --in SESSIONNAME --out mysavedsession\
"

help_saver_load="Usage: scs load [options]\n\n\
Load saved session from a file.\n\n\
Options:\n\
-i --in  <savefile>\n\
  \tspecify source savefile (by default last saved file)\n\
-o --out  <sessionname>\n\
  \tspecify target Screen session (by default current session\n\
-x --exact\n\
  \tload session with the same window numbers, move existing windows\n\
  \tto OTHER_WINDOWS group and delete existing layouts\n\
-X --exact-kill\n\
  \tsame as exact, but kill all existing windows\n\
-F --force-start  <windows>\n\
    a comma separeted list of windows which will start programs immediately,\n\
    using keyword \"all\" causes all loaded windows to start their subprograms\n\
    without waiting for user confirmation\n\
-H --no-scroll  <windows>\n\
    a comma separeted list of windows which will not load scrollbacks,\n\
    using keyword \"all\" affects all windows\n\
-r --restore\n\
  \treturn to previous window and layout after session loading\n\
-y --no-layout\n\
  \tdisable layout loading\n\
-m --mru\n\
  \trestore Most Recently Used order of windows\n\
--log  <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
  \n\
Example:\n\
$ screen-session load --exact --in mysavedsession --out SESSIONNAME\
"

def run(argv):
    if False:
        print(help_regions)
        print(help_kill_zombie)
        print(help_kill_cgroup)
        print(help_dir)
        print(help_dump)
        print(help_grab)
        print(help_group)
        print(help_manager)
        print(help_nest)
        print(help_renumber)
        print(help_sort)
        print(help_name)
        print(help_saver_modes)

    try:
        mode=argv[1]
    except:
        mode='help'
    if mode=='help':
        print(version_str+'\n')
        print(help_help)
    elif mode=='--version':
        pass
    elif mode=='regions':
        print(help_regions)
    elif mode=='kill':
        print(help_kill)
    elif mode in ('kill-zombie','kz'):
        print(help_kill_zombie)
    elif mode in ('kill-group','kg'):
        print(help_kill_group)
    elif mode=='dir':
        print(help_dir)
    elif mode=='dump':
        print(help_dump)
    elif mode in ('find-pid','fp'):
        print(help_find_pid)
    elif mode in ('find-file','ff'):
        print(help_find_file)
    elif mode=='grab':
        print(help_grab)
    elif mode=='group':
        print(help_group)
    elif mode=='manager':
        print(help_manager)
    elif mode in ('manager-remote','mr'):
        print(help_manager_remote)
    elif mode=='nest':
        print(help_nest)
    elif mode=='renumber':
        print(help_renumber)
    elif mode=='sort':
        print(help_sort)
    elif mode=='name':
        print(help_name)
    elif mode=='ls':
        print(help_saver_ls)
    elif mode=='save':
        print(help_saver_save)
    elif mode=='load':
        print(help_saver_load)
    else:
        print('No help for mode: %s'%mode)
        return 1
    return 0

if __name__=='__main__':
    import sys
    sys.exit(run(sys.argv))

