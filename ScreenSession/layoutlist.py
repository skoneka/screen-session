#!/usr/bin/env python
import os,sys
from ScreenSaver import ScreenSaver

if __name__=='__main__':
    helper = 'python '+os.path.join(os.path.split(os.path.abspath(__file__))[0],'layoutlist_agent.py')

    session=sys.argv[1]
    try:
        if sys.argv[2]=='1':
            newlay=True
        else:
            newlay=False
    except:
        newlay=False

    if not newlay:
        try:
            if sys.argv[3]=='1':
                newwin=True
            else:
                newwin=False
        except:
            newwin=False

    try:
        height=int(sys.argv[4])
    except:
        height=0

    ss=ScreenSaver(session)
    currentlayout,currentlayoutname=ss.get_layout_number()
    if newlay:
        if ss.get_layout_new('*LAYOUTLIST'):
            ss.screen('-t layoutlist %s %s %s %s 1 1 %s'%(helper,session,None,currentlayout,height))
        else:
            curwin = ss.get_number_and_title()[0]
            ss.screen('-t layoutlist %s %s %s %s 1 0 %s'%(helper,session,curwin,currentlayout,height))
    elif newwin:
        curwin = ss.get_number_and_title()[0]
        ss.screen('-t layoutlist %s %s %s %s 1 0 %s'%(helper,session,curwin,currentlayout,height))
    else:
        import layoutlist_agent
        sys.exit(layoutlist_agent.run(session,False,False,None,currentlayout,height))

