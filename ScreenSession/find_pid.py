#!/usr/bin/env python
# file: find_pid.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: find pids in windows

import sys
import tools

session=sys.argv[1]
pids=map(int,sys.argv[2:])
for win,title in tools.find_pids_in_windows(session,pids):
    print("%s %s"%(win,title))
