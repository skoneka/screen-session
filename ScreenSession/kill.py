#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    kill.py : send a signal to the last process started in a window
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
#             Brendon Crawford https://github.com/brendoncrawford
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
import tools

session = (sys.argv)[1]

if (sys.argv)[2] != '-1':
    ctty = (sys.argv)[2]
else:
    ctty = None

try:
    mode = (sys.argv)[3]
except:
    mode = 'TERM'

try:
    win = (sys.argv)[4]
except:
    win = "-1"

if tools.kill_win_last_proc(session, win, mode, ctty):
    sys.exit(0)
else:
    sys.exit(1)
