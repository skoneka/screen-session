#!/usr/bin/env python
# file: renumber.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: renumber all windows to fill the gaps

import os,sys
import tools
session=sys.argv[1]
min=int(sys.argv[3])
max=int(sys.argv[2])

tools.sort(session,min,max)
