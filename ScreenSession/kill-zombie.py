#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    kill-zombie.py : kill all zombie windows in the session
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

tools.kill_zombie(session, tools.require_dumpscreen_window(session,
                  False), windows)
tools.cleanup()

