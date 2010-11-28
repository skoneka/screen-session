#!/usr/bin/env python

import sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import tools



if __name__=='__main__':
    session=sys.argv[1]
    ss=ScreenSaver(session)
    maxwin=int(sys.argv[2])
    minwin=int(sys.argv[3])
    try:
        maxwin=int(sys.argv[4])
    except:
        pass
    else:
        try:
            minwin=int(sys.argv[5])
        except:
            pass

    tools.dump(ss,minwin,maxwin)

