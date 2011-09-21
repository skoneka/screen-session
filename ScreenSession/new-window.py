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

primer = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                      'screen-session-primer -D')
try:
    ppid = int((sys.argv)[1])
except:
    ppid = -1
session = (sys.argv)[2]
number = (sys.argv)[3]
bRenumber = (sys.argv)[4] == '1' and True or False
tdir = (sys.argv)[5]
session_arg = '-S "%s"' % session

if bRenumber:
   cwin = sc.get_current_window(session)

if tdir == '':
    f = os.popen(SCREEN + ' %s -Q @tty' % session_arg)
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
else:
    thedir = os.path.expanduser(tdir)

command = SCREEN + ' %s -Q screen' % session_arg

if len(sys.argv) > 6:
    command += ' -t \'%s\'' % (" ").join(["%s" % v for v in (sys.argv)[6:]])
else:
    command += ' -t \'%s\'' % thedir

command += " " + primer + " " + '\'%s\'' % thedir
try:
    program = (sys.argv)[6]
    for arg in (sys.argv)[6:]:
        command += ' \'' + arg + '\''
except:
    command += ' \'' + os.getenv('SHELL') + '\''

f = os.popen(command)
nwin = f.readline().split(':')[1].strip()
f.close()

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

