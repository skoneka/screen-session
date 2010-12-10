#!/usr/bin/env python

import sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import tools



if __name__=='__main__':
    session=sys.argv[1]
    ss=ScreenSaver(session)
    tools.dump(ss)

