#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    subwindows.py : recursively print windows contained in a group
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
import util

session = (sys.argv)[1]

windows = util.expand_numbers_list((sys.argv)[2:])

(groups, subwindows) = tools.subwindows(session, tools.require_dumpscreen_window(session,
        False), windows)
print('groups:  %s' % (" ").join(["%s" % v for v in groups]))
print('windows: %s' % (" ").join(["%s" % v for v in subwindows]))
tools.cleanup()
