#!/usr/bin/env python

import os,sys,signal
import GNUScreen as sc
from ScreenSaver import ScreenSaver

def out(str,active=False):
    if active:
        sys.stdout.write(str+'\n')

bPrint=False

session=sys.argv[1]
try:
    mode=sys.argv[2]
except:
    mode='TERM'

try:
    win=sys.argv[3]
except:
    win="-1"

out('session = '+session,bPrint)
session_arg="-S %s"%session
ss=ScreenSaver(session,'/dev/null','/dev/null')
ctty=ss.get_tty(win)
pids=sc.get_tty_pids(ctty)
pid = pids[len(pids)-1]
print(pids)
print(pid)

sig=eval('signal.SIG'+mode)

os.kill(int(pid),sig)


