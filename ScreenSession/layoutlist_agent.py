#!/usr/bin/env python
import os,sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import curses

MAXTITLELEN = 11

def menu_table(screen,curlay,layinfo,laytable,pos_x,pos_y):
    curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(2,curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(3,curses.COLOR_WHITE, curses.COLOR_GREEN)
    screen.keypad(1)
    x=None
    sel_num=curlay
    last_sel_num=sel_num
    c_h = curses.color_pair(1)
    c_n = curses.A_NORMAL
    c_curlay_n = curses.color_pair(2)
    c_find = curses.color_pair(3)
    row_len=None
    col_len=None
    laytable_len = len(laytable)
    search_num=None
    search_title=''
    n_search_title=''
    searching_num=False
    searching_title=False
    status_len = 0
    errormsg=''
    findNext=0
    while True:
        if findNext and n_search_title:
            i_sel_num=int(sel_num)
            layinfo_tmp = layinfo[i_sel_num+1:]+layinfo[:i_sel_num]
            if findNext == -1:
                layinfo_tmp.reverse()
            for i,entry in enumerate(layinfo_tmp):
                num,title=entry
                try:
                    tfi = title.lower().strip().index(n_search_title.lower())
                    sel_num = num
                    break
                except:
                    continue
        elif search_num:
            bfind=False
            for i,row in enumerate(laytable):
                for j,cell in enumerate(row):
                    num,title=cell
                    if search_num:
                        if search_num==num:
                            pos_x=j
                            pos_y=i
                            bfind=True
                            break
                    if bfind:
                        break

        for i,row in enumerate(laytable):
            for j,cell in enumerate(row):
                num,title=cell
                if sel_num == last_sel_num and j==pos_x and i==pos_y:
                    color=c_h
                    sel_num = num
                    last_sel_num = sel_num
                    row_len = len(row)-1
                elif not sel_num == last_sel_num and sel_num == num:
                    pos_x=j
                    pos_y=i
                    color=c_h
                    last_sel_num = sel_num
                    row_len = len(row)-1
                elif num==curlay:
                    color=c_curlay_n
                else:
                    color=c_n
                try:
                    screen.addstr(i,j*(MAXTITLELEN+5)," %-4s%s"%(num,title),color)
                    if findNext:
                        s = n_search_title
                    else:
                        s = search_title
                    tfi = title.lower().strip().index(s.lower())
                    screen.addstr(i,j*(MAXTITLELEN+5)+5+tfi,"%s"%(title[tfi:tfi+len(s)]),c_find)
                except:
                    pass
        
        if findNext:
            findNext=0
        if not searching_num:
            search_num=None
        if not searching_title:
            search_title=None
        try:
            if searching_title or searching_num:
                if searching_title:
                    prompt='> Search: '
                else:
                    prompt='> Number: '
                if search_title:
                    search = search_title
                elif search_num:
                    search = search_num
                else:
                    search = ''
                screen.addstr(laytable_len,0,"> %-*s"%(status_len,''))
                s = "%s%sI"%(prompt,search)
                status_len=len(s)
                screen.addstr(laytable_len,0,s)
            else:
                s="> %s%-*s"%(errormsg,status_len,'')
                screen.addstr(laytable_len,0,s)
                status_len=len(s)
                errormsg=''

        except:
            pass
        screen.refresh()
        x = screen.getch()
        if  searching_num and x == ord('\n'):
            searching_num=False
        elif searching_title and x == ord('\n'):
            searching_title=False
            n_search_title = search_title
            findNext=True
        elif x == 27: # Escape key
            searching_num=False
            searching_title=False
            search_num=None
            search_title=None
            errormsg='Canceled'
        elif x == curses.KEY_BACKSPACE:
            try:
                search_num = search_num[:-1]
            except:
                pass
            try:
                search_title = search_title[:-1]
            except:
                pass
        elif searching_title:
            if x == curses.KEY_UP:
                search_title = n_search_title
            elif x == curses.KEY_DOWN:
                search_title = ''
            else:
                try:
                    search_title += chr(x)
                except:
                    pass
        elif x==ord('/'):
            searching_title = True
            search_title = '' 
        elif x==ord('\n') or x == ord(' '):
            if not sel_num:
                curses.flash()
            else:
                return sel_num
        elif x in (ord('q'),ord('Q')):
            return curlay
        elif x in (ord('n'),ord('N')):
            findNext = 1
        elif x in (ord('p'),ord('P')):
            findNext = -1
        elif x == curses.KEY_HOME:
            pos_x = 0
        elif x == curses.KEY_END:
            pos_x = len(laytable[pos_y])-1
        elif x == curses.KEY_PPAGE:
            pos_y = 0
        elif x in range(ord('0'),ord('9')+1):
            searching_num=True
            if not search_num:
                search_num = chr(x)
            else:
                try:
                    search_num += chr(x)
                except:
                    pass
        else:
            for i,row in enumerate(laytable):
                try:
                    a = row[pos_x]
                    col_len = i
                except:
                    break
            #sys.stderr.write("KEY(%d) POS(%d,%d) RLEN(%d) CLEN(%d)\n"%(x,pos_x,pos_y,row_len,col_len))
            if x == curses.KEY_NPAGE:
                pos_y = col_len
            elif x in (ord('j'), curses.KEY_DOWN):
                if pos_y < col_len:
                    pos_y += 1
                else:
                    pos_y = 0
            elif x in (ord('k'), curses.KEY_UP):
                if pos_y > 0:
                    pos_y += -1
                else:
                    pos_y = col_len
            elif x in (ord('h'), curses.KEY_LEFT):
                if pos_x > 0:
                    pos_x += -1
                else:
                    pos_x = row_len
            elif x in (ord('l'), curses.KEY_RIGHT):
                if pos_x < row_len:
                    pos_x += 1
                else:
                    pos_x = 0
            else:
                try:
                    c=chr(x)
                except:
                    c='UNKNOWN'
                errormsg='Unsupported keycode: %d \"%s\"' % (x,c)
                curses.flash()

def run(session,requirecleanup_win,requirecleanup_lay,curwin,curlay,height):
    ret = 0
    ss = ScreenSaver(session)
    if requirecleanup_win:
        wnum = os.getenv('WINDOW')
    if requirecleanup_lay:
        lnum=ss.get_layout_number()[0]

    screen = curses.initscr()

    layinfo = list(sc.gen_layout_info(ss,sc.dumpscreen_layout_info(ss)))
    pos_start=(0,0)
    if height:
        laytable=[[] for i in range(0,height)]
        prev_inum=0
        for i,lay in enumerate(layinfo):
            num,title=lay
            inum = int(num)
            #sys.stderr.write("%d %d RANGE(%s)\n"%(prev_inum,inum,range(prev_inum+1,inum)))
            for j in range(prev_inum+1,inum):
                col = j%height
                laytable[col].append(('','%-*s'%(MAXTITLELEN,'')))
            col = inum%height
            laytable[col].append((num,'%-*s'%(MAXTITLELEN,title[:MAXTITLELEN])))
            if curlay==num:
                row = len(laytable[col])-1
                pos_start=(row,col)
            prev_inum=inum
    else:
        y,x = screen.getmaxyx()
        maxrows = y-1
        laytable=[[] for i in range(0,maxrows)]
        prev_inum=0
        for i,lay in enumerate(layinfo):
            num,title=lay
            col = i%maxrows
            laytable[col].append((num,title[:MAXTITLELEN]))
            if curlay==num:
                row = len(laytable[col])-1
                pos_start=(row,col)
    sc.cleanup()

    curses.start_color()
    curses.noecho()
    #screen.notimeout(1)
    #curses.init_pair(3,curses.COLOR_RED, curses.COLOR_WHITE)
    #screen.bkgd(' ',curses.color_pair(3))

    try:
        choice = menu_table(screen,curlay,layinfo,laytable,pos_start[0],pos_start[1])
    except Exception,x:
        import traceback
        traceback.print_exc(file=sys.stderr)
        choice = curlay
        ret = 1
    curses.endwin()
    if requirecleanup_lay:
        ss.command_at(False,'eval "layout select %s" "layout remove %s" "at \"%s\#\" kill"'%(choice,lnum,wnum))
    elif requirecleanup_win:
        ss.command_at(False,'eval "select %s" "layout select %s" "at \"%s\#\" kill"'%(curwin,choice,wnum))
    else:
        ss.layout('select %s'%choice,False)
    return ret

if __name__=='__main__':
    session=sys.argv[1]

    try:
        curwin=sys.argv[2]
    except:
        curwin=None

    try:
        curlay=sys.argv[3]
    except:
        curlay,currentlayoutname=ss.get_layout_number()

    try:
        if sys.argv[4]=='1':
            requirecleanup_win=True
        else:
            requirecleanup_win=False
    except:
        requirecleanup_win=False

    try:
        if sys.argv[5]=='1':
            requirecleanup_lay=True
        else:
            requirecleanup_lay=False
    except:
        requirecleanup_lay=False


    try:
        height=int(sys.argv[6])
    except:
        height=20

    run(session, requirecleanup_win, requirecleanup_lay, curwin, curlay, height)

