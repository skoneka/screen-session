#!/usr/bin/env python

import sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import tools



if __name__=='__main__':
    session=sys.argv[1]
    showpid=sys.argv[2]
    reverse=sys.argv[3]
    sort=sys.argv[4]
    try:
        groupids=sys.argv[5:]
    except:
        groupids=[]
    if showpid=='0':
        showpid=False
    else:
        showpid=True
    if reverse=='0':
        reverse=True
    else:
        reverse=False
    if sort=='0':
        sort=False
    else:
        sort=True
    ss=ScreenSaver(session)
    tools.dump(ss,showpid,reverse,sort,groupids)

