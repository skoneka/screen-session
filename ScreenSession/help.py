#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    help.py : screen-session help system
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

VERSION = '(devel)'
version_str = \
    "screen-session %s - a collection of tools for GNU Screen." % \
    VERSION

'''
broken/unfinished tools:
    grab  - grab a process and attach it to current tty
          (requires injcode)
    sort  - sort windows by title
    manager-remote -

Unpractical/useless tools:
    find-pid  - find PIDs in windows (greping dump tool output is better)
'''

help_help = """\
%s
Usage:   screen-session [mode] [options]

Help:    scs help [mode]

Options supported by all tools:
    -S [target] - target Screen session name
    -h  --help  - print detailed mode's help

Environment variables:
    SCREENBIN   - GNU Screen executable path
    PYTHONBIN   - Python interpreter path
    STY         - target Screen session name
    SCSTMPDIR   - (fixit)

Session saver modes:
    save        - save Screen ( and VIM ) session
    load        - load session
    ls          - list saved sessions

Other tools:
    dump        - print informations about windows in the session
    group       - move windows to a group
    kill        - send a signal to the last process started in a window
    kill-group  - recursively kill a group and all windows inside
    kill-zombie - kill all zombie windows in the session
    layoutlist  - display a browseable list of layouts in the session
    layout-checkpoint - record a snapshot of the current layout
    layout-history - display saved snapshots of the current layout
    layout-redo - load a snapshot of the current layout
    layout-undo - load a snapshot of the current layout
    layout-zoom - zoom into and out of a region
    manager     - a sessions manager with a split Screen window preview
    name        - get or set the sessionname
    nest-layout - nest a layout in the current region
    new-window  - open a new Screen window with the same working directory
    regions     - display a number in each region (tmux display-panes)
    renumber    - renumber windows to fill the gaps
    subwindows  - print windows contained in a group
    (undoc) raise-window
    (undoc) run-or-raise
    (undoc) run-or-raise-and-quit
    (undoc) send-escape
    (undoc) edit-buffer
    (undoc) edit-colon
    (undoc) show-buffer

Please report bugs to http://github.com/skoneka/screen-session/issues\
""" % version_str

help_regions = """\
Usage: screen-session regions [options]
       scs r
       :bind X at 0 exec scs regions

Display a number in each region.
Allows selecting, swapping and rotating. Inspired by tmux display-panes.
Requires an active layout.

Keys:
goto region  - number and [g] or ['] or [space]
swap regions - number and [s]
rotate left  - number and [l]
rotate right - number and [r]

reverse goto region     - number and [G]
swap regions and select - number and [S]
rotate left  and select - number and [L]
rotate right and select - number and [R]

Note: regions tool may appear late if there is no hardstatus line\
"""

help_kill = """\
Usage: screen-session kill [options] [signal=TERM] [window=current]
       scs K

Kill last process started in a window.
Useful for closing random emacs/vim instances and hung up ssh clients.
WARNING: sending KILL signal to the current window may crash Screen.

Options:
-t [tty device]

Example:
scs kill TERM 3
"""

help_kill_zombie = """\
Usage: screen-session kill-zombie [options] [group_ids]
       scs kz

Kill all zombie windows in session. Optionally specify target groups.\
"""

help_kill_group = """\
Usage: screen-session kill-group [options] [groupNum0] [groupNum..]
       scs kg

Recursively kill groups and windows inside.
Accepts titles and window numbers as arguments.
A dot "." selects current window, 2 dots ".."  select current group.
Take extra care with this command.\
"""

help_new_window = """\
Usage: screen-session new-window [options] [program]
       scs new
       scs nw
       :bind c eval "colon" "stuff \\"at 0 exec scs new-window \\""
       :bind -k k5 at 0 exec scs new-window -a0 key_F5

Start a new Screen window with the same working directory as the current window.

Options:
-d [dir]       - specify the working directory
-t [title]     - specify the title
-g [group]     - set the group
-n [win_num]   - set the window number
-N             - automatically set the new window number to (current number + 1)
-m [win_num]   - specify the source window
-D [dir]       - specify the directory used with -a (default: $HOME/.alter)
-a [position]  - prepend a directory specified with -D and current directory to
                 [program], useful for making directory specific keybindings

e.g. while current working directory is set to "/tmp"

:bind -k k5 at 0 exec scs new-window -a0 key_F5
is almost like
:bind -k k5 at 0 exec scs new-window $HOME/.alter/tmp/key_F5

:bind -k k5 at 0 exec scs new-window -a1 $EDITOR key_F5
is almost like
:bind -k k5 at 0 exec scs new-window $EDITOR $HOME/.alter/tmp/key_F5

If the -a flag was set then, before creating a new window, the script
tests whether the generated path exists and climbs the directory tree
if the file was not found. If the root is reached and no file was found
the path will be set to the first tested path.

An example "key_F5" script, which opens a new window inside "NOTIFY" group
and tries to raise a window running "inotail -f .*". If no matching window
was found, it will execute the command.

#!/bin/sh
scs nw -g NOTIFY scs run-or-raise-and-quit inotail -f $HOME/.screen_messages
screen -p $WINDOW -X kill\
"""

help_dump = """\
Usage: screen-session dump [options] [window_ids]
       scs d

Print informations about windows in session (MRU order by default).
A dot "." selects current window, 2 dots ".."  select current group.

Options:
-P   - do not show pid data
-r   - reverse the output
-s   - sort by window number\
"""

_help_find_pid = """\
Usage: screen-session find-pid [options] [PIDs]
       scs fp

Find PIDs in windows. Obsoleted by "dump" tool.
Example: screen-session find-pid $(pgrep vim)\
"""

_help_find_file = """\
Usage: screen-session find-file [options] [files]
       scs ff

Find open files in windows. Requires lsof.

Example:
tail -f /var/log/dmesg
scs find-file /var/log/dmesg\
"""

_help_grab = """\
Grab a process and attach to the current tty.
Works with applications without complicated output scheme.
A simple demonstration of injcode tool by Thomas Habets.
http://blog.habets.pp.se/2009/03/Moving-a-process-to-another-terminal

Usage: screen-session grab [PID]
and on the previous shell type:
$ disown
It works more reliably if commands from the script are typed manually."""

help_group = """\
Usage: screen-session group [options] [GROUP] [windows]
       scs g
       :bind G eval "colon" "stuff \\"at 0 exec scs group \\""

Move windows to a group.
If no windows given, move the current window.\
"""

#help_manager="Usage: screen-session manager [options]\n\

help_manager = """\
Usage: screen-session manager [account@host]
       scs m

Sessions manager for GNU Screen with preview in a split window.
Requires python 2.5+

KEYS:
CTRL + g  - default escape key
ALT + t   - toggle between regions
ALT + e   - step into a selected session
ALT + q   - quit
Alt + w   - wipe

COMMANDS:
? or h          - display help
q[uit]          - exit session manager
e[nter]         - enter into a session
a[ttach] [name] - attach and select
d[etach] [name] - detach and deselect
n[ame] [name]   - rename
s[creen] [args] - create session
save [output]   - save session
w[ipe]          - wipe dead sessions
restart         - restart session manager
r[efresh]       - refresh session list
l[ayout]        - toggle layout
kill K          - kill selected session
"""

_help_manager_remote = """\
Usage: screen-session manager-remote

Sessions manager for GNU Screen with preview in a split window and
support for multiple hosts. Requires python 2.5+\
"""

help_nest = """\
Usage: screen-session nest-layout [options] [TARGET_LAYOUT]
       scs nl
       :bind N eval "colon" "stuff \\"at 0 exec scs nest-layout \\""

Nest a layout in the current region.\
"""

help_layoutlist = """\
Usage: screen-session layoutlist [options] [HEIGHT]
       scs ll
       :bind l at 0 exec scs layoutlist -l -c 20

Displays a browseable list of layouts. There are two list creation algorithms.
If HEIGHT != 0, an alternative list creation algorithm is used. Layout numbers
are modulo divided by HEIGHT and the reminder determines their Y position.
This tool comes handy after raising the maximum number of layouts 
(see ":maxlay" Screen command).

Options:
-a [min_len=2]  - minimum matching charecters for auto highlight,
                  min_len = 0 disables auto highlight
-c              - do not terminate layoutlist after selecting a layout
                  or reselect a running layoutlist, best used with "-l" option,
                  there should be running only one layoutlist started with "-c"
                  per session
-l              - create a temporary layout and window for layoutlist
-M              - select previous layout and exit
-p              - run layout-checkpoint before activating layoutlist
-w              - create a temporary window for layoutlist
-t [width=11]   - set title width

Keys:
?               - display help
ENTER           - confirm / select
ARROWS and hjkl - movement
/ or SPACE      - start searching layout titles
n and p         - next / previous search result
NUMBER          - move to a layout
r or C-c or C-l - refresh the layout list
m or a          - toggle MRU view,
v               - toggle search/autohighlight results view
o               - toggle current and selected layouts
q               - quit / select previous layout
Q               - force quit if "-c" option was used

Note: If you are using -c and -l options and layoutlist stopped working
      properly, then delete the temporary directory:
      /tmp/screen-session-$USER/___layoutlist

See also: layout-checkpoint, layout-zoom\
"""


help_layout_checkpoint = """\
Usage: screen-session layout-checkpoint [options] 
       scs lc

Record a snapshot of the current layout.
Either run it frequently or integrate it with keybindings.

Example:
    bind S eval "split" "at 0 exec screen-session layout-checkpoint"

See also: layoutlist, layout-undo, layout-redo, layout-history\
"""

help_layout_undo= """\
Usage: screen-session layout-undo [options] [step = 1] 
       scs lu

Load a snapshot of the current layout,
step = 0 indicates the current snapshot, step = 1 the previous snapshot, ...

See also: layout-checkpoint, layout-redo, layout-history\
"""

help_layout_redo= """\
Usage: screen-session layout-redo [options] [step = 1] 
       scs lr

Load a snapshot of the current layout,
step = 0 indicates the current snapshot, step = 1 the previous snapshot, ...

See also: layout-checkpoint, layout-undo, layout-history\
"""

help_layout_history= """\
Usage: screen-session layout-history [options] 
       scs lh

Display saved snapshots of the current layout.

See also: layout-checkpoint, layout-undo, layout-redo\
"""

help_layout_zoom= """\
Usage: screen-session layout-zoom [options] 
       scs lz
       :bind o at 0 exec scs layout-zoom

Zoom into and out of a region. Intended to replace ":only" command.
Requires an active layout. Inspired by ZoomWin Vim plugin:
http://www.vim.org/scripts/script.php?script_id=508

See also: layout-checkpoint, layout-undo, layout-redo\
"""

help_renumber = """\
Usage: screen-session renumber [options]

Renumber windows to fill the gaps.\
"""

_help_sort = """\
Usage: screen-session sort [options]

Sort windows by titles.\
"""

help_subwindows = """\
Usage: screen-session subwindows [groupids or titles]
       scs sw

Print windows contained in groups.
A dot "." selects current window, 2 dots ".."  select current group.\
"""

help_name = """\
Usage: screen-session name [options] [new_sessionname]
       scs n

Get or set the sessionname.\
"""
help_saver_other = """\
Usage: screen-session other [options] 

Auxiliary mode, used mainly by screen-session-primer.

Options:
--pack [target]
    archive unpacked savefile ( which must be accessible from --dir )
--unpack [savefile]
    unpack savefile to /tmp/screen-session-$USER
-l --log  [file]
    output to a file instead of stdout and stderr
-d --dir  [directory = $HOME/.screen-sessions]
    directory holding saved sessions

See also: save, load, ls\
"""

help_saver_ls = """\
Usage: screen-session save [-S sessionname] [options] [savefile_filter]

List saved sessions.

Options:
-l --log  [file]
    output to a file instead of stdout and stderr
-d --dir  [directory = $HOME/.screen-sessions]
    directory holding saved sessions

See also: save, load, other\
"""

help_saver_save = """\
Usage: screen-session save [-S sessionname] [options] [target_savefile]
       :bind S at 0 exec screen -mdc /dev/null screen-session save -fS $PID.$STY

Save GNU Screen and VIM sessions to a file. Dump shell envvars.
Howto: http://adb.cba.pl/gnu-screen-tips-page-my.html#howto-screen-session

Options:
-f --force
    force saving even if a savefile with the same name already exists
-e --exclude  [windows]
    a comma separated list of windows to be ignored during saving,
    if a window is a group all nested windows are also included
-L --exclude-layout  [layouts]
    a comma separated list of layouts to be ignored during saving,
-H --no-scroll  [windows]
    a comma separated list of windows which scrollbacks will be ignored,
    if a window is a group all nested windows are also included,
    using keyword "all" affects all windows
-y --no-layout
    disable layout saving
-V --no-vim
    disable vim session saving
-W --no-shellvars
    disable dumping of shell envvars
-l --log [file]
    output to a file instead of stdout and stderr
-d --dir  [directory = $HOME/.screen-sessions]
    directory holding saved sessions

Examples:
#1# save Screen named SESSIONNAME as mysavedsession
screen-session save -S SESSIONNAME mysavedsession
#2# save the current session, force overwrite of old savefiles
scs save --force
#3# save the current session without layouts and without window "SECURE" scroll
scs save --no-layout --no-scroll SECURE
#4# run session saver after 3 minutes of inactivity
:idle 180 at 0 exec scs save --force --log /dev/null
#5# an alternative binding
bind S eval 'colon' 'stuff "at 0 exec screen -mdc /dev/null scs save -fS \\"$PID.$STY\\""'

See also: load, ls, other\
"""

help_saver_load = """\
Usage: screen-session load [-S sessionname] [options] [source_savefile]

Load saved session from a file.
Howto: http://adb.cba.pl/gnu-screen-tips-page-my.html#howto-screen-session

Options:
-x --exact
    load session with the same window numbers, move existing windows,
    to OTHER_WINDOWS group and delete existing layouts
-X --exact-kill
    same as exact, but also kill all existing windows
-F --force-start  [windows]
    a comma separated list of windows which will start programs immediately,
    using keyword "all" causes all loaded windows to start their subprograms
    without waiting for user's confirmation
-y --no-layout
    disable layout loading
-n --no-group-wrap
    do not wrap windows in RESTORE_* or OTHER_WINDOWS_* groups
-m --mru
    enable restoring of the Most Recently Used order of windows
-l --log  [file]
    output to a file instead of stdout and stderr
-d --dir  [directory = $HOME/.screen-sessions]
    directory holding saved sessions

Examples:
#1# restore mysavedsession inside Screen named SESSIONNAME
screen-session load -S SESSIONNAME --exact mysavedsession
#2# load the last saved session inside the current Screen session
scs load
#3# load the last saved session with exactly the same window numbers
scs load --exact
#4# load inside the current session without layouts and start all subprograms
scs load --no-layout --force-start all
#5# load the last saved session into a new Screen
screen -m scs load --exact-kill

See also: save, ls, other\
"""


def run(argv):
    try:
        mode = argv[1]
    except:
        mode = 'help'
    try:
        if mode in ('help', 'h', '-h', '--help'):
            print(help_help)
        elif mode == '--version':
            print(version_str)
        elif mode in ('regions', 'r'):
            print(help_regions)
        elif mode in ('kill', 'K'):
            print(help_kill)
            import inspect
            import signal
            print(("\nSignals:"))
            for (name, obj) in inspect.getmembers(signal):
                if name.startswith('SIG'):
                    print(name[3:])
        elif mode in ('kill-zombie', 'kz'):
            print(help_kill_zombie)
        elif mode in ('kill-group', 'kg'):
            print(help_kill_group)
        elif mode in ('dir', 'new', 'new-window', 'nw'):
            print(help_new_window)
        elif mode in ('dump', 'd'):
            print(help_dump)
        elif mode in ('find-pid', 'fp'):
            print(_help_find_pid)
        elif mode in ('find-file', 'ff'):
            print(_help_find_file)
        elif mode == 'grab':
            print(_help_grab)
        elif mode in ('group', 'g'):
            print(help_group)
        elif mode in ('manager', 'm'):
            print(help_manager)
        elif mode in ('manager-remote', 'mr'):
            print(_help_manager_remote)
        elif mode in ('nest', 'nest-layout', 'nl'):
            print(help_nest)
        elif mode in ('layoutlist', 'll'):
            print(help_layoutlist)
        elif mode in ('layout-checkpoint', 'lc'):
            print(help_layout_checkpoint)
        elif mode in ('layout-undo', 'lu'):
            print(help_layout_undo)
        elif mode in ('layout-redo', 'lr'):
            print(help_layout_redo)
        elif mode in ('layout-history', 'lh'):
            print(help_layout_history)
        elif mode in ('layout-zoom', 'lz'):
            print(help_layout_zoom)
        elif mode == 'renumber':
            print(help_renumber)
        elif mode == 'sort':
            print(_help_sort)
        elif mode in ('subwindows', 'sw'):
            print(help_subwindows)
        elif mode in ('name', 'n'):
            print(help_name)
        elif mode == 'ls':
            print(help_saver_ls)
        elif mode == 'save':
            print(help_saver_save)
        elif mode == 'load':
            print(help_saver_load)
        elif mode == 'other':
            print(help_saver_other)
        else:
            print('No help for mode: %s' % mode)
            return 1
    except IOError:
        pass
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(run(sys.argv))

