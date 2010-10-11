#!/usr/bin/env python
# file: renumber.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: renumber all windows to fill the gaps

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

wins=[]
wins_trans={}
all_win=list(sc.gen_all_windows(min,max,session))
for win,type,title in all_win:
    iwin=int(win)
    wins.append((ss.get_group(win),iwin,type))
    #wins_trans[iwin]=iwin

win_biggest=wins[len(wins)-1][1]
for i in range(0,win_biggest+1):
    wins_trans[i]=i

wins.sort(key=lambda wins:wins[0])

i=0
for group,win,type in wins:
    if wins_trans[win]!=i:
        #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
        ss.number(str(i),str(wins_trans[win]))
        tmp=wins_trans[win]
        wins_trans[win]=wins_trans[i]
        wins_trans[i]=tmp
    i+=1
