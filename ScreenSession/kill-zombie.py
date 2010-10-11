#!/usr/bin/env python
# file: kill-zombie.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill all zombie window in a Screen session

import os,sys,signal
import GNUScreen as sc
from ScreenSaver import ScreenSaver

session=sys.argv[1]

try:
    max=sys.argv[3]
except:
    max=sys.argv[2]
max=int(max)

try:
    min=sys.argv[4]
except:
    min=0
min=int(min)

session_arg="-S %s"%session
ss=ScreenSaver(session,'/dev/null','/dev/null')

for win,type,title in sc.gen_all_windows(min,max,session):
    if type==-1:
        ss.kill('',win)


