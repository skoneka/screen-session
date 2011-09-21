#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    sort.py :  sort windows by title; currently broken, it should be rewritten
#               with support for selecting groups through tools.subwindows()
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
import tools
session = (sys.argv)[1]
tools.sort(session, tools.require_dumpscreen_window(session, False))
tools.cleanup()
