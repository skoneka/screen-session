#!/usr/bin/env python

VERSION='git'
version_str="SCREEN-SESSION (%s) - a collection of tools for GNU Screen."%VERSION

help_help="\
Usage:\t scs [mode] [options]\n\
\t scs [mode] -S session [options]\n\
\n\
Help:\t scs [mode] --help\n\
\n\
Global Options:\n\
    -S [target]\t- target Screen session\n\
    -W\t\t- wait for keypress\n\
    \n\
Available modes:\n\
    save\t- save session to disk\n\
    load\t- load session from file\n\
    ls\t\t- list saved sessions\n\
    \n\
    dir\t\t- start Screen window in the same working directory\n\
    dump\t- dump informations about windows in session\n\
    grab\t- grab a process and attach it to current tty\n\
    \t\t  (requires injcode)\n\
    group\t- move windows to a group\n\
    kill\t- send signal to last process started in a window\n\
    kill-cgroup\t- kill all windows in the current group\n\
    kill-zombie\t- kill all zombie windows in session\n\
    manager\t- sessions manager with split screen preview\n\
    name\t- get or set sessionname\n\
    nest\t- nest layout in the current region\n\
    regions\t- display number in each region\n\
    \t\t  (like tmux display-panes)\n\
    renumber\t- renumber windows to fill gaps\n\
    sort\t- sort windows by title\n\
    \n\
Report bugs to http://github.com/skoneka/screen-session/issues\
    "

help_regions="Display number in each region.\n\
Reassembles the functionality of tmux display-panes.\n\
\nUsage: screen-session regions [options]"

help_kill="Kill last process started in a window.\n\
Useful for closing random emacs/vim instances.\n\
\nUsage: screen-session kill [options] [signal=TERM] [window=current]"

help_kill_zombie="Kill all zombie windows in session.\n\
\nUsage: screen-session kill-zombie [options] [maxwin=MAXWIN] [minwin=0]"

help_kill_cgroup="Recursively kill all windows in the current group.\n\
It does not kill the group itself and the window from which it was started.\n\
Take care with this command.\n\
\nUsage: screen-session kill-cgroup [options] [more windows to kill]"

help_dir="Start a new Screen window in the same working directory\n\
on the position next to the current window.\n\
\nUsage: screen-session dir [options] [program]"

help_dump="Dump informations about windows in session.\n\
\nUsage: screen-session dump [options] [maxwin] [minwin]"

help_grab="Grab a process and attach to the current tty.\n\
Works with applications without complicated output scheme.\n\
Require. injcode by Thomas Habets.\n\
\nUsage: screen-session grab [PID]\n\
on the previous shell type: $ disown"

help_group="Move windows to a group.\n\
If no windows given, moves current window.\n\
\nUsage: screen-session group [options] [GROUP] [windows]"

help_manager="Sessions manager for GNU Screen with preview in a split window.\n\
\nUsage: screen-session manager"

help_nest="Nest layout in the current region.\n\
\nUsage: screen-session nest [options] [TARGET_LAYOUT]"

help_renumber="Renumber windows to fill the gaps.\n\
\nUsage: screen-session renumber [options] [maxwin=MAXWIN] [minwin=0]"

help_sort="Sort windows by titles.\n\
\nUsage: screen-session sort [options] [maxwin=MAXWIN] [minwin=0]"

help_name="Try to get the current sessionname.\n\
\nUsage: screen-session name [options] [new_sessionname]"

help_saver_modes='GNU Screen session saver.\n\
Usage: screen-session [save|load|ls] [options]'

help_saver='Options:\n\
ls\n\
  \tlist saved sessions\n\
load\n\
  \tloading mode\n\
save\n\
  \tsaving mode\n\
-i --in     <session or directory>\n\
  \tsessionname(saving) or savefile(loading)\n\
-o --out    <session or directory>\n\
  \tsessionname(loading) or savefile(saving)\n\
-m --maxwin <number>\n\
  \tsupply biggest window number in your session\n\
-f --force  <number>\n\
  \tforce saving even if savefile with the same\n\
  \talready exists name exists\n\
-x --exact\n\
  \tload session with the same window numbers, move existing windows\n\
  \tto OTHER_WINDOWS group and delete existing layouts\n\
-r --restore\n\
  \treturn to home window and home layout after session loading\n\
-y --no-layout\n\
  \tdisable layout saving/loading\n\
-V --no-vim\n\
  \tdisable vim session saving\n\
-I --idle <seconds>\n\
  \tstart command after <seconds> of inactivity\n\
--log       <file>\n\
  \toutput to file instead stdout\n\
-d --dir\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
-W\n\
  \twait for any key when finished. Has to be the first option after mode\n\
-h --help\n\
  \tshow this message\n\
  \n\
Examples:\n\
$ screen-session save --maxwin 20 --in SESSIONNAME --out mysavedsession\n\
$ screen-session load --exact --in mysavedsession --out SESSIONNAME\n\
\n'

'''
broken:
-X --exact-kill-other\n\
  \tsame as exact, but kills all existing windows\n\
'''

if __name__=='__main__':
    import sys
    print(version_str+'\n')
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
        mode=sys.argv[1]
    except:
        mode='help'
    if mode=='help':
        print(help_help)
    elif mode=='--version':
        pass
    elif mode=='regions':
        print(help_regions)
    elif mode=='kill':
        print(help_kill)
    elif mode=='kill-zombie':
        print(help_kill_zombie)
    elif mode=='kill-cgroup':
        print(help_kill_cgroup)
    elif mode=='dir':
        print(help_dir)
    elif mode=='dump':
        print(help_dump)
    elif mode=='grab':
        print(help_grab)
    elif mode=='group':
        print(help_group)
    elif mode=='manager':
        print(help_manager)
    elif mode=='nest':
        print(help_nest)
    elif mode=='renumber':
        print(help_renumber)
    elif mode=='sort':
        print(help_sort)
    elif mode=='name':
        print(help_name)
    elif mode=='save' or mode=='load' or mode=='ls':
        print(help_saver_modes)
        print(help_saver)

    else:
        print('No help for mode: %s'%mode)

