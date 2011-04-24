#!/usr/bin/env python

VERSION='git'
version_str="SCREEN-SESSION (%s) - a collection of tools for GNU Screen."%VERSION


help_help="\
Usage:\t screen-session [mode] [options]\n\
\t scs [mode] -S session [options]\n\
Help:\t scs [mode] --help\n\
     \t scs help [mode]\n\
Global Options:\n\
    -S [target]\t- target Screen session name\n\
Saver modes:\n\
    save\t- save session to disk\n\
    load\t- load session from file\n\
    ls  \t- list saved sessions\n\
Other tools:\n\
    dump\t- print informations about windows in session\n\
    find-file\t- find files in windows\n\
    group\t- move windows to a group\n\
    kill\t- send signal to last process started in a window\n\
    kill-group\t- kill a group and all windows inside\n\
    kill-zombie\t- kill all zombie windows in session\n\
    manager\t- sessions manager with split screen preview\n\
    name\t- get or set sessionname\n\
    nest-layout\t- nest a layout in the current region\n\
    new-window\t- open a Screen window with the same working directory\n\
    regions\t- display a number in each region (tmux display-panes)\n\
    renumber\t- renumber windows to fill the gaps\n\
    subwindows\t- print windows contained in a group\n\
Report bugs to http://github.com/skoneka/screen-session/issues\
"
'''
broken/unfinished tools:
    grab\t- grab a process and attach it to current tty\n\
    \t\t  (requires injcode)\n\
    sort\t- sort windows by title\n\
    manager-remote - 

unpractial/useless tools:
    find-pid\t- find PIDs in windows (greping dump tool output is better)\n\
'''

help_regions="Usage: screen-session regions [options]\n\
       scs r [options]\n\n\
Display a number in each region.\n\
Allows selecting, swapping and rotating. Inspired by tmux display-panes.\n\
\n\
Keys:\n\
goto region  -> number and <g> or <'> or <space>\n\
swap regions -> number and <s>\n\
rotate left  -> number and <l>\n\
rotate right -> number and <r>\n\
\n\
reverse goto region     -> number and <G>\n\
swap regions and select -> number and <S>\n\
rotate left  and select -> number and <L>\n\
rotate right and select -> number and <R>\
"

help_kill="Usage: screen-session kill [options] [signal=TERM] [window=current]\n\n\
Kill last process started in a window.\n\
Useful for closing random emacs/vim instances.\
"

help_kill_zombie="Usage: screen-session kill-zombie [options] [groupids]\n\
       screen-session kz [options] [groupids]\n\n\
Kill all zombie windows in session. Optionally specify target groups.\
"

help_kill_group="Usage: screen-session kill-group [options] [groupNum0] [groupNum..]\n\
       screen-session kg [options] [groupNum0] [groupNum..]\n\n\
Recursively kill groups and windows inside.\n\
Accepts group window numbers as arguments.\n\
If the first argument is \"current\" kill the current group.\n\
If the first argument is \"all\" kill all groups in the session.\n\
Take extra care with this command.\
"

help_new_window="Usage: screen-session new-window [options] [program]\n\
       screen-session new [options] [program]\n\
       screen-session dir [options] [program]\n\n\
Start a new Screen window in the same working directory\n\
on the position next to the current window.\
"

help_dump="Usage: screen-session dump [options] [window_ids]\n\
       scs d [options] [window_ids]\n\n\
Print informations about windows in session (most recently used first).\n\
-P \t- do not show pid data\n\
-r \t- reverse the output\n\
-s \t- sort by window number\
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

help_nest="Usage: screen-session nest-layout [options] [TARGET_LAYOUT]\n\
       screen-session nl [options] [TARGET_LAYOUT]\n\n\
Nest a layout in the current region.\
"

help_renumber="Usage: screen-session renumber [options]\n\n\
Renumber windows to fill the gaps.\
"

help_sort="Usage: screen-session sort [options]\n\n\
Sort windows by titles.\
"

help_subwindows="Usage: screen-session subwindows [groupids or titles]\n\
       screen-session sw [groupids or titles]\n\n\
Print windows contained in groups.\
"

help_name="Usage: screen-session name [options] [new_sessionname]\n\n\
Get or set sessionname.\
"

help_saver_modes='GNU Screen session saver.\n\
Usage: screen-session [save|load|ls] [-S sessionname] [options] [savefile]'

help_saver_ls="Usage: screen-session save [-S sessionname] [options] [savefile_filter]\n\n\
Garden of Eden Creation Kit for GNU Screen.\n\
List saved sesssions.\n\
Options:\n\
-l --log  <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\
"

help_saver_save="Usage: screen-session save [-S sessionname] [options] [target_savefile]\n\n\
Garden of Eden Creation Kit for GNU Screen.\n\
Save GNU Screen and VIM sessions to a file.\n\
Options:\n\
-f --force\n\
  \tforce saving even if savefile with the same name already exists\n\
-e --exclude  <windows>\n\
  \ta comma separated list of windows to be ignored during saving,\n\
  \tif a window is a group all subwindows are also included\n\
-H --no-scroll  <windows>\n\
  \ta comma separeted list of windows which scrollbacks will be ignored,\n\
  \tif a window is a group all subwindows are also included,\n\
  \tusing keyword \"all\" affects all windows\n\
-y --no-layout\n\
  \tdisable layout saving\n\
-V --no-vim\n\
  \tdisable vim session saving\n\
-l --log <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
Example:\n\
$ screen-session save -S SESSIONNAME mysavedsession\
"

help_saver_load="Usage: screen-session load [-S sessionname] [options] [source_savefile]\n\n\
Garden of Eden Creation Kit for GNU Screen.\n\
Load saved session from a file.\n\
Options:\n\
-x --exact\n\
  \tload session with the same window numbers, move existing windows\n\
  \tto OTHER_WINDOWS group and delete existing layouts\n\
-X --exact-kill\n\
  \tsame as exact, but kill all existing windows\n\
-F --force-start  <windows>\n\
    a comma separeted list of windows which will start programs immediately,\n\
    using keyword \"all\" causes all loaded windows to start their subprograms\n\
    without waiting for user confirmation\n\
-r --restore\n\
  \treturn to previous window and layout after session loading\n\
-y --no-layout\n\
  \tdisable layout loading\n\
-n --no-group-wrap\n\
  \tdo not wrap windows in RESTORE_* or OTHER_WINDOWS_* groups\n\
-m --mru\n\
  \trestore Most Recently Used order of windows\n\
-l --log  <file>\n\
  \toutput to a file instead of stdout\n\
-d --dir  <directory>\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
Example:\n\
$ screen-session load -S SESSIONNAME --exact mysavedsession\
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
    if mode in ('help','h'):
        print(version_str+'\n')
        print(help_help)
    elif mode=='--version':
        print(version_str)
    elif mode in ('regions','r'):
        print(help_regions)
    elif mode=='kill':
        print(help_kill)
    elif mode in ('kill-zombie','kz'):
        print(help_kill_zombie)
    elif mode in ('kill-group','kg'):
        print(help_kill_group)
    elif mode in ('dir','new','new-window'):
        print(help_new_window)
    elif mode in ('dump','d'):
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
    elif mode in ('nest','nest-layout','nl'):
        print(help_nest)
    elif mode=='renumber':
        print(help_renumber)
    elif mode=='sort':
        print(help_sort)
    elif mode in ('subwindows','sw'):
        print(help_subwindows)
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

