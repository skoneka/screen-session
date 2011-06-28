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

    try:
        height=int(sys.argv[3])
    except:
        height=20

    ss=ScreenSaver(session)
    currentlayout,currentlayoutname=ss.get_layout_number()
    if newlay and ss.get_layout_new('layout_list'):
        ss.screen('-t layoutlist %s %s %s 1 %s'%(helper,session,currentlayout,height))
    ## This is a bit faster but it does not check whether there are free layouts, so it may end removing the current layout during cleanup
    #if newlay:
        #ss.command_at(False,'eval \"layout new\" \"screen -t layoutlist %s %s %s 1 %s\"'%(helper,session,currentlayout,height))

    else:
        import layoutlist_agent
        sys.exit(layoutlist_agent.run(session,False,currentlayout,height))



