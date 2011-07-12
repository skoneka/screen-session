#!/usr/bin/env python
import os,sys,signal
import GNUScreen as sc
from util import tmpdir
from ScreenSaver import ScreenSaver
import curses


MAXTITLELEN = 11
NO_END = False


def handler(signum,frame):
    pass

def menu_table(ss,screen,tmplay,curwin,curlay,layinfo,laytable,pos_x,pos_y,height):
    global MAXTITLELEN
    curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(2,curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(3,curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(4,curses.COLOR_RED, curses.A_NORMAL)
    norm = curses.A_NORMAL
    bold = curses.A_BOLD
    dim  = curses.A_DIM
    screen.keypad(1)
    x=None
    last_sel_num = sel_num_before_search = sel_num = curlay
    c_h = curses.color_pair(1) | bold
    c_n = norm
    c_curlay_n = curses.color_pair(2)
    c_find = curses.color_pair(3)
    c_error = curses.color_pair(4)
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
        keyboard_int = False
        if findNext and n_search_title:
            i_sel_num=int(sel_num)
            layinfo_tmp = layinfo[i_sel_num+1:]+layinfo[:i_sel_num]
            if findNext == -1:
                layinfo_tmp.reverse()
            for i,entry in enumerate(layinfo_tmp):
                try:
                    num = entry[0]
                    title = entry[1]
                except:
                    title = ""
                try:
                    tfi = title.lower().strip().index(n_search_title.lower())
                    sel_num = num
                    break
                except:
                    continue
        elif searching_num:
            bfind=False
            if not search_num:
                sn = sel_num_before_search
                searching_num = False
            else:
                sn = search_num
            for i,row in enumerate(laytable):
                for j,cell in enumerate(row):
                    num,title=cell
                    if sn:
                        if sn == num:
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
                    color = c_h
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
                    screen.addstr(i,j*(MAXTITLELEN+5)+5+tfi,"%s"%(title[tfi:tfi+len(s)]), c_find)
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
                screen.addstr(laytable_len,0,"> %-*s"%(status_len,''),c_n)
                s = "%s%sI"%(prompt,search)
                status_len=len(s)
                screen.addstr(laytable_len,0,s,c_n)
            else:
                screen.addstr(laytable_len,0,"> %-*s"%(status_len,''),c_n)
                s="%s"%(errormsg)
                screen.addstr(laytable_len, 2, s, c_error|bold)
                status_len=len(s)
                errormsg=''

        except:
            pass
        screen.refresh()
        x = screen.getch()
        
        if x == -1 or ( x in (ord('r'),ord('R')) and not searching_title and not searching_num):
            searching_title = False
            searching_num = False
            try:
                try:
                    try:
                        if NO_END:
                            f = open( lock_and_com_file, 'r' )
                            from string import strip as str_strip
                            #pid,cwin,clay,MAXTITLELEN,height = map( str_strip,f.readlines() )
                            nd = map( str_strip,f.readlines() )
                            curwin = nd[3]
                            curlay = nd[4]
                            MAXTITLELEN = int(nd[5])
                            height = int(nd[6])
                            f.close()
                            screen.erase()
                    except:
                        pass
                    layinfo = list(sc.gen_layout_info(ss,sc.dumpscreen_layout_info(ss)))
                    laytable,pos_start = create_table(ss, screen, curlay, layinfo, tmplay, height)
                    laytable_len = len(laytable)
                    errormsg = 'Refreshed'
                finally:
                    sc.cleanup()
            except:
                errormsg = 'Layouts dumping error.'
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
                if len(search_num) == 0:
                    raise Exception
                search_num = search_num[:-1]
            except:
                searching_num = False
                pass
            try:
                if len(search_title) == 0:
                    raise Exception
                search_title = search_title[:-1]
            except:
                searching_title = False
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
            searching_num=False
            if not sel_num:
                curses.flash()
                errormsg = "No layout selected."
            elif sel_num == tmplay:
                curses.flash()
                errormsg = "This IS layout %s."%sel_num
            else:
                if NO_END:
                    if curwin != '-1':
                        ss.command_at(False,'eval "select %s" "layout select %s" "layout title"'%(curwin,sel_num))
                    else:
                        ss.command_at(False,'eval "layout select %s" "layout title"'%(sel_num))
                else:
                    return sel_num
        elif x in (ord('q'),ord('Q')):
            if NO_END and x == ord('q'):
                ss.command_at(False,'eval "layout select %s" "layout title"'%(sel_num))
            else:
                return curlay
        elif x in (ord('n'),ord('N')):
            findNext = 1
        elif x in (ord('p'),ord('P')):
            findNext = -1
        elif x in (curses.KEY_HOME, ord('^')):
            pos_x = 0
        elif x in (curses.KEY_END, ord('$')):
            pos_x = len(laytable[pos_y])-1
        elif x == curses.KEY_PPAGE:
            pos_y = 0
        elif x == ord('?'):
            from help import help_layoutlist
            screen.erase()
            for i,line in enumerate(help_layoutlist.split('\n')):
                screen.addstr(i,0," %s"%(line),c_n)
            screen.refresh()
            x = screen.getch()
        elif x in range(ord('0'),ord('9')+1):
            if not searching_num:
                searching_num = True
                sel_num_before_search = sel_num
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
def create_table_std(ss, screen, curlay, layinfo, lnum):
    pos_start=(0,0)
    y,x = screen.getmaxyx()
    maxrows = y-1
    laytable=[[] for i in range(0,maxrows)]
    prev_inum=0
    for i,lay in enumerate(layinfo):
        try:
            num = lay[0]
            title = lay[1]
        except:
            title = ""
        col = i%maxrows
        if num == lnum:
            title = '*'+title
        laytable[col].append((num,title[:MAXTITLELEN]))
        if curlay==num:
            row = len(laytable[col])-1
            pos_start=(row,col)
    return laytable, pos_start

def create_table_mod(ss, screen, curlay, layinfo, lnum, height):
    pos_start=(0,0)
    laytable=[[] for i in range(0,height)]
    prev_inum=0
    for i,lay in enumerate(layinfo):
        try:
            num = lay[0]
            title = lay[1]
        except:
            title = ""
        inum = int(num)
        #sys.stderr.write("%d %d RANGE(%s)\n"%(prev_inum,inum,range(prev_inum+1,inum)))
        for j in range(prev_inum+1,inum):
            col = j%height
            laytable[col].append(('','%-*s'%(MAXTITLELEN,'')))
        col = inum%height
        if num == lnum:
            title = '*'+title
        laytable[col].append((num,'%-*s'%(MAXTITLELEN,title[:MAXTITLELEN])))
        if curlay==num:
            row = len(laytable[col])-1
            pos_start=(row,col)
        prev_inum=inum
    return laytable,pos_start

def create_table(ss, screen, curlay, layinfo, lnum, height):
    if height:
        return create_table_mod(ss, screen, curlay, layinfo, lnum, height)
    else:
        return create_table_std(ss, screen, curlay, layinfo, lnum)



def run(session,requirecleanup_win,requirecleanup_lay,curwin,curlay,height):
    global lock_and_com_file
    signal.signal(signal.SIGINT,handler)

    ret = 0
    ss = ScreenSaver(session)
    if requirecleanup_win:
        wnum = os.getenv('WINDOW')
    if requirecleanup_lay:
        lnum=ss.get_layout_number()[0]
    else:
        lnum=None

    if NO_END:
        lock_and_com_file = os.path.join(tmpdir,'___layoutlist_%s'%session)
        f = open( lock_and_com_file, 'w')
        f.write(str(os.getpid())+'\n')
        if requirecleanup_win and not requirecleanup_lay:
            f.write(wnum+'\n')
        else:
            f.write('-1\n')
        if requirecleanup_lay:
            f.write(lnum+'\n')
        else:
            f.write('-1\n')
        f.close()

    try:
        try:
            layinfo = list(sc.gen_layout_info(ss,sc.dumpscreen_layout_info(ss)))
        finally:
            sc.cleanup()
    except:
        sys.stderr.write('Layouts dumping error.\n')
        return 1
    screen = curses.initscr()
    laytable,pos_start = create_table(ss, screen, curlay, layinfo, lnum, height)

    curses.start_color()
    curses.noecho()
    #screen.notimeout(1)
    #curses.init_pair(3,curses.COLOR_RED, curses.COLOR_WHITE)
    #screen.bkgd(' ',curses.color_pair(3))

    try:
        choice = menu_table(ss,screen,lnum,curwin,curlay,layinfo,laytable,pos_start[0],pos_start[1],height)
        if requirecleanup_lay and choice == lnum:
            choice = curlay
    except Exception,x:
        import traceback
        traceback.print_exc(file=sys.stderr)
        choice = curlay
        ret = 1
    curses.endwin()
    from util import remove
    remove(lock_and_com_file)
    if requirecleanup_lay:
        ss.command_at(False,'eval "layout select %s" "layout remove %s" "at \"%s\#\" kill" "layout title"'%(choice,lnum,wnum))
    elif requirecleanup_win:
        ss.command_at(False,'eval "select %s" "layout select %s" "at \"%s\#\" kill" "layout title"'%(curwin,choice,wnum))
    else:
        ss.command_at(False,'eval "layout select %s" "layout title"'%(choice))
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
        if sys.argv[6]=='1':
            NO_END = True
        else:
            NO_END = False
    except:
        NO_END = False


    try:
        MAXTITLELEN = int(sys.argv[7])
    except:
        MAXTITLELEN = 11

    try:
        height = int(sys.argv[8])
    except:
        height = 20

    run(session, requirecleanup_win, requirecleanup_lay, curwin, curlay, height)

