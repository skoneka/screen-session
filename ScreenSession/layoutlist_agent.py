#!/usr/bin/env python
import os,sys
import GNUScreen as sc
from ScreenSaver import ScreenSaver
import curses

MAXTITLELEN = 10

def menu_dumb(curlay,laytable):
    for row in laytable:
        print row
    print ('layout list..(current %s)'%curlay)
    inp = raw_input('\nInput: ')
    choice = int(inp)
    return choice

def menu_table(screen,curlay,laytable,pos_x,pos_y):
    curses.init_pair(1,curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(2,curses.COLOR_RED, curses.COLOR_GREEN)
    screen.keypad(1)
    x=None
    sel_num=curlay
    c_h = curses.color_pair(1)
    c_n = curses.A_NORMAL
    c_curlay_n = curses.color_pair(2)
    while x!= ord('\n'):
        screen.addstr(1,1,'menu: ')
        for i,row in enumerate(laytable):
            for j,cell in enumerate(row):
                num=cell[0]
                title=cell[1]
                if j==pos_x and i==pos_y:
                    color=c_h
                    sel_num = num
                elif num==curlay:
                    color=c_curlay_n
                else:
                    color=c_n
                screen.addstr(i,j*(MAXTITLELEN+5),"%-4s%s"%(num,title),color)
        screen.refresh()
        x = screen.getch()
        if x==ord('\n') or x == ord(' '):
            return sel_num

        elif x==ord('j') or x == curses.KEY_DOWN:
            if pos_y < 19:
                pos_y += 1
            else:
                pos_y = 1
        elif x == ord('k') or x == curses.KEY_UP:
            if pos_y > 0:
                pos_y += -1
            else:
                pos_y = 19
        elif x == ord('h') or x == curses.KEY_LEFT:
            pos_x += -1
        elif x == ord('l') or x == curses.KEY_RIGHT:
            pos_x += 1
        elif x in (ord('q'),ord('Q')):
            return curlay
        else:
            curses.flash()

def run(session,requirecleanup,curlay,height):
    ret = 0
    ss = ScreenSaver(session)
    if requirecleanup:
        num = ss.get_number_and_title()[0]
    layinfo = list(sc.gen_layout_info(ss,sc.dumpscreen_layout_info(ss)))
    laytable=[[] for i in range(0,height)]
    pos_start=(0,0)
    for i,lay in enumerate(layinfo):
        num=lay[0]
        title=lay[1]
        col = i%height
        laytable[col].append((num,title[:MAXTITLELEN]))
        if curlay==num:
            row = len(laytable[col])-1
            pos_start=(row,col)
    screen = curses.initscr()
    curses.start_color()
    try:
        choice = menu_table(screen,curlay,laytable,pos_start[0],pos_start[1])
    except Exception,x:
        import traceback
        traceback.print_exc(file=sys.stderr)
        choice = curlay
        ret = 1
    curses.endwin()
    #print ('select: %s'%choice)
    
    if True:
        if requirecleanup:
            ss.layout('remove',False)

        ss.layout('select %s'%choice)

        if requirecleanup:
            ss.kill(num)
    return ret

if __name__=='__main__':
    session=sys.argv[1]
    try:
        curlay=sys.argv[2]
    except:
        curlay,currentlayoutname=ss.get_layout_number()

    try:
        if sys.argv[3]=='1':
            requirecleanup=True
        else:
            requirecleanup=False
    except:
        requirecleanup=False
    try:
        height=int(sys.argv[4])
    except:
        height=20
    run(session,requirecleanup,curlay,height)

