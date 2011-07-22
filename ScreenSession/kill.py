#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    kill.py : send a signal to the last process started in a window
#
#    Copyright (C) 2010-2011 Artur Skonecki
#
#    Authors: Artur Skonecki http://github.com/skoneka
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
try:
    mode = (sys.argv)[2]
except:
    mode = 'TERM'

try:
    win = (sys.argv)[3]
except:
    win = "-1"

ret = tools.kill_win_last_proc(session, win, mode)
exit(0 if ret else 1)
