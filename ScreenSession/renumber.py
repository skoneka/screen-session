#!/usr/bin/env python
# file: renumber.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: renumber all windows to fill the gaps

import os,sys
import GNUScreen as sc

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

sc.renumber(session,min,max)
