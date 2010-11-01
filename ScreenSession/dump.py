#!/usr/bin/env python

import sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import tools



if __name__=='__main__':
    session=sys.argv[1]
    ss=ScreenSaver(session)
    try:
        maxwin=int(sys.argv[2])
    except:
        maxwin=ss.maxwin()
        minwin=0
    else:
        try:
            minwin=int(sys.argv[3])
        except:
            minwin=0
    tools.dump(ss,minwin,maxwin)

