#!/usr/bin/env python
# file: kill.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill the foremost process in a window

import os,sys,signal
import GNUScreen as sc
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


tools.kill_win_last_proc(session,win,mode)


