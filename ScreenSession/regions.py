#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    regions.py : display a number in each region (like tmux display-panes);
#                 select, swap and rotate regions
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

import sys
import os
import time
import signal
import tempfile
import pwd
import copy
from util import tmpdir, tmpdir_source, remove
import GNUScreen as sc
from GNUScreen import SCREEN
from ScreenSaver import ScreenSaver
from six.moves import range

inputfile = "___regions-input-%d" % os.getpid()
sourcefile = os.path.join(tmpdir_source, "regions-source-%d" % os.getpid())
subprogram = 'screen-session-helper'
subprogram_args = '-nh'


def local_copysign(x, y):
    """Return x with the sign of y. Backported from Python 2.6."""

    if y >= 0:
        return x * (1 - 2 * int(x < 0))
    else:
        return x * (1 - 2 * int(x >= 0))


def rotate_list(l, offset):
    """
    Rotate a list by (offset) elements. Elements which fall off
    one side are provided again on the other side.
    Returns a rotated copy of the list. If (offset) is 0,
    returns a copy of (l).

    Examples:
        >>> rotate_list([1, 2, 3, 4, 5, 6], 2)
        [3, 4, 5, 6, 1, 2]
        >>> rotate_list([1, 2, 3, 4, 5, 6], -2)
        [5, 6, 1, 2, 3, 4]
    """

    if len(l) == 0:
        raise ValueError("Must provide a list with 1 or more elements")
    if offset == 0:
        rv = copy.copy(l)
    else:
        real_offset = offset % int(local_copysign(len(l), offset))
        rv = l[real_offset:] + l[:real_offset]
    return rv


handler_lock = False


def handler(signum, frame):
    global handler_lock
    if handler_lock:
        return
    else:
        handler_lock = True
    global win_history
    bSelect = False
    mode = -1
    number = 0
    try:
        f = open(inputfile, "r")
        ch = f.readline()
        f.close()
        remove(inputfile)
        try:
            number = int(ch[1:])
        except:
            number = 0

        if ch[0] == 's':
            mode = 1
        elif ch[0] == 'S':
            mode = 1
            bSelect = True
        elif ch[0] == " " or ch[0] == "'" or ch[0] == 'g' or ch[0] == 'G':
            mode = 0
            bSelect = True
            if ch[0] == 'G':
                number = -1 * number
        elif ch[0] == "l":
            mode = 2
            rnumber = number
        elif ch[0] == "L":
            mode = 2
            rnumber = number
            number = -1 * number
            bSelect = True
        elif ch[0] == "r":
            rnumber = -1 * number
            mode = 2
        elif ch[0] == "R":
            rnumber = -1 * number
            mode = 2
            bSelect = True
        else:
            mode = 0

        if number != 0 and mode == 1:
            tmp = win_history[0]
            win_history[0] = win_history[number]
            win_history[number] = tmp
        elif mode == 2:
            win_history = rotate_list(win_history, rnumber)
    except IOError:
        sys.stderr.write('No input file found.\n')

    cleanup()

    if number != 0 and bSelect:

        # this will work properly up to 62 regions (MAXSTR-4)/8

        command = SCREEN + ' -S "%s" -X eval' % session
        if number < 0:
            number = abs(number)
            cfocus = 'focus prev'
        else:
            cfocus = 'focus'
        for i in range(0, number):
            command += ' "%s"' % cfocus
        os.system(command)
    sys.exit(0)


def cleanup():
    cmd = ''
    f = open(sourcefile, 'w')
    for (i, w) in enumerate(win_history):
        if w == "-1":
            w = "-"
        f.write("""select %s
at \"%s\#\" kill
focus
""" % (w, wins[i]))
    f.flush()
    f.close()
    scs.source(sourcefile)
    scs.focusminsize(focusminsize)
    sc.cleanup()
    remove(sourcefile)

def prepare_windows(scs):
    global focusminsize
    regions = None
    regions = sc.get_regions(sc.dumpscreen_layout(scs.pid))
    sc.cleanup()
    focusminsize = "%s %s" % (regions.focusminsize_x, regions.focusminsize_x)
    regions_c = len(regions.regions)
    focus_offset = regions.focus_offset
    scs.focusminsize('0 0')
    this_win_history = []
    cmd = ''
    f = open(sourcefile, 'w')
    for i in range(0, regions_c):
        f.write("""screen -t scs-regions-helper %s %s %s %d
focus
""" %
                (subprogram, subprogram_args, inputfile, i))
    f.flush()
    f.close
    scs.source(sourcefile, "screen-session regions")
    remove(sourcefile)

    regions_n = []
    regions_n = sc.get_regions(sc.dumpscreen_layout(scs.pid))
    sc.cleanup()

    for r in (regions.regions)[focus_offset:]:
        this_win_history.append(r[0])
    for r in (regions.regions)[:focus_offset]:
        this_win_history.append(r[0])

    new_windows = []
    for r in (regions_n.regions)[focus_offset:]:
        new_windows.append(r[0])
    for r in (regions_n.regions)[:focus_offset]:
        new_windows.append(r[0])

    return (this_win_history, new_windows, regions_c)


if __name__ == '__main__':
    if not os.path.exists(tmpdir_source):
        os.makedirs(tmpdir_source)

    inputfile = os.path.join(tmpdir, inputfile)
    subprogram = os.path.join(os.path.dirname((sys.argv)[0]), subprogram)

    session = (sys.argv)[1]
    scs = ScreenSaver(session)
    (win_history, wins, regions_c) = prepare_windows(scs)

    signal.signal(signal.SIGUSR1, handler)
    signal.pause()

