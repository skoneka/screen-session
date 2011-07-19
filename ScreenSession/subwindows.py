#!/usr/bin/env python
#
#    subwindows.py : recursively print windows contained in a group
#
#    Copyright (C) 2010-2011 Artur Skonecki
#
#    Authors: Artur Skonecki <admin [>at<] adb.cba.pl>
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

session=sys.argv[1]
try:
    groupids=sys.argv[2]
    groupids=sys.argv[2:]
except:
    groupids=['all']
groups,windows=tools.subwindows(session,tools.require_dumpscreen_window(session,False), groupids)
print ('groups:  %s'%(" ".join(["%s"%v for v in groups])))
print ('windows: %s'%(" ".join(["%s"%v for v in windows])))
tools.cleanup()
