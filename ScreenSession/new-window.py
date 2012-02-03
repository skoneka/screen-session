#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    new-window.py : open a new Screen window with the same working directory
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

import os
import sys
import platform
import GNUScreen as sc
from GNUScreen import SCREEN

ARGSNUM = 10

primer = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                      'screen-session-primer -D')
try:
    ppid = int((sys.argv)[1])
except:
    ppid = -1
session = (sys.argv)[2]
sourcenumber = (sys.argv)[3]
number = (sys.argv)[4]
bRenumber = (sys.argv)[6] == '1' and True or False
tdir = (sys.argv)[6]
tgroup = (sys.argv)[7]
altdir = (sys.argv)[8]
altdir_pos = (sys.argv)[9]

session_arg = '-S "%s"' % session

if bRenumber:
    cwin = sc.get_current_window(session)

if tdir.startswith('/') or tdir.startswith('~'):
    thedir = os.path.expanduser(tdir)
else:
    if sourcenumber == "-1":
        f = os.popen(SCREEN + ' %s -Q @tty' % session_arg)
    else:
        f = os.popen(SCREEN + ' %s -p %s -Q @tty' % (session_arg, sourcenumber))
    ctty = f.readline()
    f.close()
    if ctty.startswith('/dev'):
        if platform.system() == 'FreeBSD':
            pids = sc.get_tty_pids(ctty)
        else:
            pids = sc._get_tty_pids_pgrep(ctty)

        try:
            p_i = [i for (i, x) in enumerate(pids) if x == ppid][0] - 1
            thepid = pids[p_i]
        except:
            p_i = len(pids) - 1
            thepid = pids[p_i]

        info = None
        while not info and p_i >= 0:
            try:
                info = sc.get_pid_info(thepid)
            except:
                p_i -= 1
                thepid = pids[p_i]
        thedir = info[0]
    else:
        thedir = os.getcwd()
    thedir = os.path.join(thedir,tdir)

command = SCREEN + ' %s -Q screen' % session_arg

if len(sys.argv) > ARGSNUM:
    if altdir_pos != '-1':
        d = os.path.realpath(thedir)[1:]
        ap = int(altdir_pos)
        while True:
            s = os.path.join(altdir, d, sys.argv[ARGSNUM+ap])
            if not os.path.exists(s):
                if d == '':
                    s = os.path.join(altdir, os.path.realpath(thedir)[1:], sys.argv[ARGSNUM+ap])
                    break
                d = os.path.dirname(d)
            else:
                break
        sys.argv[ARGSNUM+ap] = s
    command += r""" -t '%s'""" % (" ").join(["%s" % v for v in (sys.argv)[ARGSNUM:]])
else:
    command += r""" -t '%s'""" % thedir

command += " " + primer + " " + r"""'%s'""" % thedir
try:
    program = (sys.argv)[ARGSNUM]
    for arg in (sys.argv)[ARGSNUM:]:
        command += " '" + arg + "'"
except:
    command += " '" + os.getenv('SHELL') + "'"

f = os.popen(command)
nwin = f.readline().split(':')[1].strip()
f.close()

if tgroup != '-1':
    os.spawnv(os.P_WAIT, SCREEN , ['screen', '-S', session, '-X', 'group', tgroup])

if nwin != '-1':
    if number != '-1':
        sc.move(int(nwin), int(number), True, session)
        print(number)
    elif bRenumber:
        targ_num = int(cwin) + 1
        sc.move(int(nwin), targ_num, True, session)
        print(targ_num)
else:
    print(nwin)

