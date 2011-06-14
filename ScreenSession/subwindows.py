#!/usr/bin/env python
# file: subwindows.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: print windows inside groups 

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
