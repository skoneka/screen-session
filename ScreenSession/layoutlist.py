#!/usr/bin/env python
import os,sys
from util import tmpdir
from ScreenSaver import ScreenSaver

if __name__=='__main__':
    helper = os.getenv('PYTHONBIN')+' '+os.path.join(os.path.split(os.path.abspath(__file__))[0],'layoutlist_agent.py')

    session=sys.argv[1]
    try:
        if sys.argv[2]=='1':
            newlay=True
        else:
            raise Exception
    except:
        newlay=False

    try:
        if sys.argv[3]=='1':
            newwin=True
        else:
            raise Exception
    except:
        newwin=False

    try:
        s_no_end = sys.argv[4]
        if sys.argv[4]=='1':
            no_end = True
        else:
            raise Exception
    except:
        s_no_end = '0'
        no_end = False

    try:
        title_width=int(sys.argv[5])
    except:
        title_width = 11
    
    E_AUTOSEARCH = sys.argv[6]

    try:
        height=int(sys.argv[7])
    except:
        height=0

    ss=ScreenSaver(session)

    if no_end: 
        lock_and_com_file = os.path.join(tmpdir,'___layoutlist_%s'%session.split('.',1)[0])
        if os.path.exists(lock_and_com_file):
            try:
                f = open( lock_and_com_file, 'r' )
                pid = f.readline().strip()
                tmpwin = f.readline().strip()
                tmplay = f.readline().strip()
                cwin = f.readline().strip()
                if tmpwin != '-1':
                    cwin = ss.get_number_and_title()[0]
                else:
                    cwin = '-1'
                clay = f.readline().strip()
                clay = ss.get_layout_number()[0]
                f.close()
                f = open( lock_and_com_file, 'w' )
                f.write(pid+'\n'+tmpwin+'\n'+tmplay+'\n'+cwin+'\n'+clay+'\n'+str(title_width)+'\n'+str(height))
                f.close()
                from signal import SIGINT
                os.kill(int(pid),SIGINT)
                if tmplay!= '-1':
                    ss.command_at(False,'layout select %s'%(tmplay))
                elif tmpwin != '-1':
                    ss.command_at(False,'select %s'%(tmpwin))
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)
                pass
            else:
                sys.exit(0)

    currentlayout,currentlayoutname=ss.get_layout_number()
    if newlay:
        if ss.get_layout_new('LAYOUTLIST'):
            ss.screen('-t layoutlist %s %s %s %s 1 1 %s %s %s %s'%(helper,session,None,currentlayout,s_no_end,title_width,E_AUTOSEARCH,height))
        else:
            curwin = ss.get_number_and_title()[0]
            ss.screen('-t layoutlist %s %s %s %s 1 0 %s %s %s %s'%(helper,session,curwin,currentlayout,s_no_end,title_width,E_AUTOSEARCH,height))
    elif newwin:
        curwin = ss.get_number_and_title()[0]
        ss.screen('-t layoutlist %s %s %s %s 1 0 %s %s %s %s'%(helper,session,curwin,currentlayout,s_no_end,title_width,E_AUTOSEARCH, height))
    else:
        import layoutlist_agent
        layoutlist_agent.MAXTITLELEN = title_width
        layoutlist_agent.NO_END = no_end
        layoutlist_agent.E_AUTOSEARCH = True if E_AUTOSEARCH=='1' else False
        sys.exit(layoutlist_agent.run(session,False,False,None,currentlayout,height))

