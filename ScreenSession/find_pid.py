#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    find_pid.py : find pids in windows; obsoleted by dump.py
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
import tools
from six.moves import map

session = (sys.argv)[1]
pids = list(map(int, (sys.argv)[2:]))
for (win, title) in tools.find_pids_in_windows(session, tools.require_dumpscreen_window(session,
        False), pids):
    print("%s %s" % (win, title))
tools.cleanup()
