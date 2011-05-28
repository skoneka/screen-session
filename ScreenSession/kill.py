#!/usr/bin/env python
# file: kill.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill the foremost process in a window

import sys
import tools

session=sys.argv[1]
try:
    mode=sys.argv[2]
except:
    mode='TERM'

try:
    win=sys.argv[3]
except:
    win="-1"


ret = tools.kill_win_last_proc(session,win,mode)
exit(0 if ret else 1)
