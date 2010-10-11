#!/usr/bin/env python
# file: kill-zombie.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill all zombie window in a Screen session

import os,sys,signal
import tools

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

tools.kill_zombie(session,min,max)

