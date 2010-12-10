#!/usr/bin/env python
# file: find_file.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: find files in windows

import sys
import tools

session=sys.argv[1]
files=sys.argv[2:]

pids=tools.find_files_in_pids(files)
pids=map(int,pids)
for win,title in tools.find_pids_in_windows(session,pids):
    print("%s %s"%(win,title))
