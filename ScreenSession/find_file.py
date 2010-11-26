#!/usr/bin/env python
# file: find_file.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: find files in windows

import sys
import tools

session=sys.argv[1]
min=int(sys.argv[3])
max=int(sys.argv[2])
files=sys.argv[4:]

pids=tools.find_files_in_pids(min,max,files)
pids=map(int,pids)
for win,title in tools.find_pids_in_windows(session,min,max,pids):
    print("%s %s"%(win,title))
