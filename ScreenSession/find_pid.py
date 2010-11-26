#!/usr/bin/env python
# file: find_pid.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: find pids in windows

import sys
import tools

session=sys.argv[1]
min=int(sys.argv[3])
max=int(sys.argv[2])
pids=map(int,sys.argv[4:])

for win in tools.find_pids_in_windows(session,min,max,pids):
    print(win)
