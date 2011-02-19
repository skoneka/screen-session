#!/usr/bin/env python

import sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import tools



if __name__=='__main__':
    session=sys.argv[1]
    showpid=sys.argv[2]
    try:
        groupids=sys.argv[3:]
    except:
        groupids=[]
    if showpid=='0':
        showpid=False
    else:
        showpid=True
    ss=ScreenSaver(session)
    tools.dump(ss,showpid,groupids)

