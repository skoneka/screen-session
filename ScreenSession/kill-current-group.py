#!/usr/bin/env python
# file: kill-group.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill recursively all windows in the current group

import sys
import tools
from ScreenSaver import ScreenSaver

session=sys.argv[1]
args=sys.argv[2:]
wins=[]
for arg in args:
    wins.append(arg)

ss=ScreenSaver(session,'/dev/null','/dev/null')
tools.kill_current_group(ss,True,wins,-1)
