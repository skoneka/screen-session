#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    sessionname.py : get or set the sessionname, it qualifies for a rewrite
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
import GNUScreen as sc
from util import timeout_command
from GNUScreen import SCREEN

# sessions must have a display (must be attached) to be detected


def get_sessionname(session=None):
    if session:
        session_arg = '-S \"%s\"' % session
    else:
        session_arg = ''
    p = os.popen(SCREEN + ' %s -X sessionname' % session_arg).close()
    s = timeout_command(SCREEN + ' %s -Q @lastmsg' % session_arg, 3)[0]
    return s.split('\'', 1)[1].rsplit('\'', 1)[0]


try:
    if (sys.argv)[1] != "__no__session__":
        session = (sys.argv)[1]
    else:
        raise Exception
except:
    session = None
try:
    s = get_sessionname(session)
except:
    s = None
    s2 = None
    try:
        badname = os.getenv('STY').split('.', 1)[0]
        if not badname:
            session = None
            raise Exception
        sclist = sc.get_session_list()
        for (sc, active) in sclist:
            if sc.startswith(badname):
                s = sc
                if not sc.endswith('-queryA'):
                    break
                    None
    except:
        pass
if s:
    try:
        if session and s.find(session) > -1:
            newname = (sys.argv)[2]
            os.popen(SCREEN + ' -S \"%s\" -X sessionname \"%s\"' % (s,
                     newname)).close()
        else:
            raise Exception
    except:
        if not session or s.find(session) > -1:
            print(s)
            sys.exit(0)
        else:
            print("__no__session__")
            sys.exit(1)
else:
    print("__no__session__")
    sys.exit(1)

