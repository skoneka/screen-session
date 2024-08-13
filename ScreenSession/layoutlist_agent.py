#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    layoutlist.py : display a browseable list of layouts in the session
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import signal
import pickle
import GNUScreen as sc
from util import tmpdir
from ScreenSaver import ScreenSaver
import curses
from six.moves import map
from six.moves import range

AUTOSEARCH_MIN_MATCH = 2
MAXTITLELEN = 11
NO_END = False


def handler(signum, frame):
    pass

#class menu_table_namespace: 
#    # TODO: use it for nonlocal variables in menu_table nested functions
#    pass

def menu_table(
    ss,
    screen,
    tmplay,
    curwin,
    curlay,
    layinfo,
    laytable,
    pos_x,
    pos_y,
    height,
    ):
    global MAXTITLELEN
    global mru_file
    (y, x) = screen.getmaxyx()

    # default background colors

    try:
        curses.use_default_colors()
    except:
        pass

    ## custom background
    #curses.init_pair(1,curses.COLOR_WHITE, curses.COLOR_BLACK)
    #screen.bkgd(' ',curses.color_pair(1))

    # ?universal? color scheme

    curses.init_pair(2, -1, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(4, -1, curses.COLOR_GREEN)
    curses.init_pair(5, -1, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)
    curses.init_pair(7, curses.COLOR_RED, curses.COLOR_YELLOW)
    curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLUE)
    curses.init_pair(9, curses.COLOR_RED, curses.COLOR_GREEN)

    c_h = curses.color_pair(2) | curses.A_BOLD
    c_n = curses.A_NORMAL
    c_curlay_n = curses.color_pair(3) | curses.A_BOLD
    c_find = curses.color_pair(4)
    c_error = curses.color_pair(5) | curses.A_BOLD
    c_project = curses.color_pair(6) | curses.A_BOLD
    c_h_project = curses.color_pair(7)
    c_curlay_project = curses.color_pair(8) | curses.A_BOLD
    c_find_project = curses.color_pair(9)
    screen.keypad(1)
    x = None
    other_num = last_sel_num = sel_num_before_search = sel_num = curlay
    row_len = None
    col_len = None
    search_num = None
    search_title = ""
    n_search_title = ""
    searching_num = False
    searching_title = False
    b_force_sel_num = False
    status_len = 0
    errormsg = ""
    findNext = 0
    current_view = 'n'
    try:
        mru_layouts = pickle.load(open(mru_file, 'r'))
    except:
        mru_layouts = []
    view_layouts = []
    pos_x_c = pos_y_c = layinfo_c = laytable_c = None

    def mru_add(layout_num):
        layout_title = ""
        index = None
        for (i, lay) in enumerate(mru_layouts):
            (num, title) = lay
            if num == layout_num:
                index = i
                break
        if index != None:
            mru_layouts.pop(index)
        for lay in layinfo:
            try:
                num = lay[0]
                title = lay[1]
            except:
                title = ""
            if num == layout_num:
                layout_title = title
                break
        mru_layouts.insert(0, (layout_num, layout_title))
        pickle.dump(mru_layouts, open(mru_file, 'w'))

    mru_add(curlay)
    while True:
        view_layouts = []
        keyboard_int = False
        if findNext and n_search_title:
            layinfo_pos = 0
            for (k, e) in enumerate(layinfo):
                if e[0] == sel_num:
                    layinfo_pos = k
            layinfo_tmp = layinfo[layinfo_pos + 1:] + layinfo[:layinfo_pos]
            if findNext == -1:
                layinfo_tmp.reverse()
            for (i, entry) in enumerate(layinfo_tmp):
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
            bfound = False
            if not search_num:
                sn = sel_num_before_search
                searching_num = False
            else:
                sn = search_num
            for (i, row) in enumerate(laytable):
                for (j, cell) in enumerate(row):
                    (num, title) = cell
                    if sn:
                        if sn == num:
                            pos_x = j
                            pos_y = i
                            bfound = True
                            break
                    if bfound:
                        break

        project_title = None
        bfound = False
        for (i, row) in enumerate(laytable):
            for (j, cell) in enumerate(row):
                (num, title) = cell
                if sel_num == last_sel_num and j == pos_x and i == pos_y and \
                    not b_force_sel_num:
                    sel_num = num
                    last_sel_num = sel_num
                    row_len = len(row) - 1
                    project_title = title.lower()
                    bfound = True
                    break
                elif (b_force_sel_num or not sel_num == last_sel_num) and \
                    sel_num == num:
                    b_force_sel_num = False
                    pos_x = j
                    pos_y = i
                    last_sel_num = sel_num
                    row_len = len(row) - 1
                    project_title = title.lower()
                    bfound = True
                    break
            if bfound:
                break
        if sel_num != curlay:
            other_num = sel_num
        bSearchResults = False
        for (i, row) in enumerate(laytable):
            for (j, cell) in enumerate(row):
                (num, title) = cell
                bsel = False
                c_f = c_find
                if sel_num == num:
                    color = c_h
                    c_p = c_h_project
                    bsel = True
                elif num == curlay:
                    color = c_curlay_n
                    c_p = c_curlay_project
                else:
                    color = c_n
                    c_p = c_project
                try:
                    screen.addstr(i, j * (MAXTITLELEN + 5), " %-4s%s" %
                                  (num, title), color)
                    tl = title.lower()
                    if AUTOSEARCH_MIN_MATCH > 0:
                        pi = 0

                        for (k, l) in enumerate(tl):
                            try:
                                if l == project_title[k]:
                                    pi += 1
                                else:
                                    break
                            except:
                                break
                        if pi >= AUTOSEARCH_MIN_MATCH:
                            if bsel:
                                screen.addstr(i, j*(MAXTITLELEN+5), " %-4s"%(num), c_p)
                            else:
                                screen.addstr(i, j*(MAXTITLELEN+5)+5, "%s"%(title[0:pi]), c_p)
                            if not bsel:
                                c_f = c_find_project

                    if findNext:
                        s = n_search_title
                    else:
                        s = search_title
                    tfi = tl.strip().index(s.lower())
                    if not bSearchResults:
                        bSearchResults = True
                        view_layouts = []
                    screen.addstr(i, j * (MAXTITLELEN + 5) + 5 + tfi,
                                  "%s" % title[tfi:tfi + len(s)], c_f)
                except:
                    pass

        if findNext:
            findNext = 0
        if not searching_num:
            search_num = None
        if not searching_title:
            search_title = None
        try:
            screen.addstr(y - 1, 0, "> %-*s" % (status_len, ""), c_n)
            if searching_title or searching_num:
                if searching_title:
                    prompt = '> Search: '
                else:
                    prompt = '> Number: '
                if search_title:
                    search = search_title
                elif search_num:
                    search = search_num
                else:
                    search = ""
                s = "%s%s" % (prompt, search)
                status_len = len(s)
                screen.addstr(y - 1, 0, s, curses.A_BOLD)
            else:
                if errormsg:
                    s = "%s" % errormsg
                    screen.addstr(y - 1, 2, s, c_error | curses.A_BOLD)
                else:
                    s = 'Press \'?\' to view help'
                    screen.addstr(y - 1, 2, s, c_n)
                status_len = len(s)
                errormsg = ""
        except:
            pass

        screen.refresh()
        x = screen.getch()

        # layout list refresh ^C ^L ^R

        if x in (-1, 12, 18) or x in (ord('r'), ord('R')) and not searching_title and \
            not searching_num:
            if laytable_c:
                current_view = 'n'
                pos_x = pos_x_c
                pos_y = pos_y_c
                pos_x_c = pos_y_c = layinfo_c = laytable_c = None
            (y, x) = screen.getmaxyx()
            searching_title = False
            searching_num = False
            try:
                try:
                    try:
                        if NO_END:
                            f = open(lock_and_com_file, 'r')
                            from string import strip as str_strip

                            #pid,cwin,clay,MAXTITLELEN,height = map( str_strip,f.readlines() )

                            nd = list(map(str_strip, f.readlines()))
                            curwin = nd[3]
                            sel_num = curlay = nd[4]
                            MAXTITLELEN = int(nd[5])
                            height = int(nd[6])
                            f.close()
                            screen.erase()
                            mru_add(curlay)
                    except:
                        pass
                    layinfo = list(sc.gen_layout_info(ss, sc.dumpscreen_layout_info(ss)))
                    (laytable, pos_start) = create_table(ss, screen,
                            curlay, layinfo, tmplay, height)
                    errormsg = 'Refreshed'
                finally:
                    sc.cleanup()
            except:
                errormsg = 'Layouts dumping error.'
        elif searching_title and x == ord('\n'):
            searching_title = False
            n_search_title = search_title
            findNext = True
        elif x == 27:

                      # Escape key

            searching_num = False
            searching_title = False
            search_num = None
            search_title = None
            errormsg = 'Canceled'
            n_search_title = search_title
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
                search_title = ""
            else:
                try:
                    search_title += chr(x)
                except:
                    pass
        elif x in (ord('/'), ord(' ')):
            searching_title = True
            searching_num = False
            search_title = ""
        elif x == ord('\n'):
            if layinfo_c:
                current_view = 'n'
                layinfo = list(layinfo_c)
                laytable = list(laytable_c)
                pos_x = pos_x_c
                pos_y = pos_y_c
                pos_x_c = pos_y_c = layinfo_c = laytable_c = None
            searching_num = False
            if not sel_num:
                curses.flash()
                errormsg = "No layout selected."
            elif sel_num == tmplay:
                curses.flash()
                errormsg = "This IS layout %s." % sel_num
            else:
                if NO_END:
                    mru_add(sel_num)
                    if curwin != '-1':
                        ss.command_at(False,
                                'eval "select %s" "layout select %s" "layout title"' %
                                (curwin, sel_num))
                    else:
                        ss.command_at(False,
                                'eval "layout select %s" "layout title"' %
                                sel_num)
                else:
                    return sel_num
        elif x in (ord('q'), ord('Q')):
            if NO_END and x == ord('q'):
                if layinfo_c:
                    current_view = 'n'
                    layinfo = list(layinfo_c)
                    laytable = list(laytable_c)
                    pos_x = pos_x_c
                    pos_y = pos_y_c
                    pos_x_c = pos_y_c = layinfo_c = laytable_c = None
                mru_add(sel_num)
                ss.command_at(False,
                              'eval "layout select %s" "layout title"' %
                              curlay)
            else:
                return curlay
        elif x in (ord('n'), ord('P')):
            findNext = 1
        elif x in (ord('p'), ord('N')):
            findNext = -1
        elif x in (curses.KEY_HOME, ord('^')):
            pos_x = 0
        elif x in (curses.KEY_END, ord('$')):
            pos_x = len(laytable[pos_y]) - 1
        elif x == curses.KEY_PPAGE:
            pos_y = pos_y - 5 > 0 and pos_y - 5 or 0
        elif x == ord('?'):
            from help import help_layoutlist
            screen.erase()
            for (i, line) in enumerate(help_layoutlist.split('\n')):
                try:
                    screen.addstr(i, 0, " %s" % line, c_n)
                except:
                    pass
            screen.refresh()
            x = screen.getch()
            screen.erase()
        elif x == ord('o'):
            if sel_num != curlay:
                other_num = sel_num
                sel_num = curlay
            else:
                sel_num = other_num
            b_force_sel_num = True
        elif x in (ord('m'), ord('a')):
            screen.erase()
            if not layinfo_c:
                current_view = 'm'
                layinfo_c = list(layinfo)
                laytable_c = list(laytable)
                layinfo = mru_layouts
                pos_x_c = pos_x
                pos_y_c = pos_y
                pos_x = pos_y = 0
                (laytable, pos_start) = create_table_std(ss, screen,
                        curlay, layinfo, tmplay)
                if len(laytable) > 1:
                    pos_y = 1
            else:
                current_view = 'n'
                b_force_sel_num = True
                layinfo = list(layinfo_c)
                laytable = list(laytable_c)
                pos_x = pos_x_c
                pos_y = pos_y_c
                pos_x_c = pos_y_c = layinfo_c = laytable_c = None
        elif x == ord('v'):
            screen.erase()
            if not layinfo_c:
                current_view = 'v'
                layinfo_c = list(layinfo)
                laytable_c = list(laytable)
                pos_x_c = pos_x
                pos_y_c = pos_y
                pos_x = pos_y = 0
                nst = n_search_title.lower()
                for lay in layinfo:
                    try:
                        num = lay[0]
                        title = lay[1]
                    except:
                        title = ""
                    tl = title.lower().strip()
                    if bSearchResults:
                        try:
                            tfi = tl.index(nst)
                            view_layouts.append((num, title))
                        except:
                            pass
                    else:
                        pi = 0
                        for (k, l) in enumerate(tl):
                            try:
                                if l == project_title[k]:
                                    pi += 1
                                else:
                                    break
                            except:
                                break
                        if pi >= AUTOSEARCH_MIN_MATCH:
                            view_layouts.append((num, title))

                (laytable, pos_start) = create_table_std(ss, screen,
                        sel_num, view_layouts, tmplay)
                (pos_x, pos_y) = pos_start
                layinfo = view_layouts
            else:
                current_view = 'n'
                b_force_sel_num = True
                layinfo = list(layinfo_c)
                laytable = list(laytable_c)
                pos_x = pos_x_c
                pos_y = pos_y_c
                pos_x_c = pos_y_c = layinfo_c = laytable_c = None
        elif x in range(ord('0'), ord('9') + 1):
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
            searching_num = False
            for (i, row) in enumerate(laytable):
                try:
                    a = row[pos_x]
                    col_len = i
                except:
                    break

            #sys.stderr.write("KEY(%d) POS(%d,%d) RLEN(%d) CLEN(%d)\n"%(x,pos_x,pos_y,row_len,col_len))

            if x == curses.KEY_NPAGE:
                pos_y = pos_y + 5 < col_len and pos_y + 5 or col_len
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
                    c = chr(x)
                except:
                    c = 'UNKNOWN'
                errormsg = 'Unsupported keycode: %d \"%s\"' % (x, c)
                curses.flash()


def create_table_std(ss, screen, curlay, layinfo, lnum):
    pos_start = (0, 0)
    (y, x) = screen.getmaxyx()
    maxrows = y - 1
    laytable = [[] for i in range(0, maxrows)]
    prev_inum = 0
    for (i, lay) in enumerate(layinfo):
        try:
            num = lay[0]
            title = lay[1]
        except:
            title = ""
        col = i % maxrows
        if num == lnum:
            title = '*' + title
        laytable[col].append((num, '%-*s' % (MAXTITLELEN, title[:MAXTITLELEN])))
        if curlay == num:
            row = len(laytable[col]) - 1
            pos_start = (row, col)
    return (laytable, pos_start)


def create_table_mod(ss, screen, curlay, layinfo, lnum, height):
    pos_start = (0, 0)
    laytable = [[] for i in range(0, height)]
    prev_inum = 0
    for (i, lay) in enumerate(layinfo):
        try:
            num = lay[0]
            title = lay[1]
        except:
            title = ""
        inum = int(num)

        #sys.stderr.write("%d %d RANGE(%s)\n"%(prev_inum,inum,range(prev_inum+1,inum)))

        for j in range(prev_inum + 1, inum):
            col = j % height
            laytable[col].append(("", '%-*s' % (MAXTITLELEN, "")))
        col = inum % height
        if num == lnum:
            title = '*' + title
        laytable[col].append((num, '%-*s' % (MAXTITLELEN, title[:MAXTITLELEN])))
        if curlay == num:
            row = len(laytable[col]) - 1
            pos_start = (row, col)
        prev_inum = inum
    return (laytable, pos_start)


def create_table(ss, screen, curlay, layinfo, lnum, height):
    if height:
        return create_table_mod(ss, screen, curlay, layinfo, lnum,
                                height)
    else:
        return create_table_std(ss, screen, curlay, layinfo, lnum)


def run(session, requirecleanup_win, requirecleanup_lay, curwin, curlay,
        height, select_other = False):
    global lock_and_com_file, mru_file
    lltmpdir = os.path.join(tmpdir, '___layoutlist')
    try:
        os.makedirs(lltmpdir)
    except:
        pass

    signal.signal(signal.SIGINT, handler)
    session = session.split('.', 1)[0]

    ret = 0
    ss = ScreenSaver(session)
    wnum = os.getenv('WINDOW')
    if requirecleanup_lay:
        lnum = ss.get_layout_number()[0]
    else:
        lnum = None

    mru_file = os.path.join(lltmpdir, '%s_MRU' % session)
    if select_other:
        mru_layouts = pickle.load(open(mru_file, 'r'))
        num, title = mru_layouts[1]
        tmp = mru_layouts[0]
        mru_layouts[0] = mru_layouts[1]
        mru_layouts[1] = tmp
        ss.command_at(False, 'eval "layout select %s" "layout title"' %
                      num)
        pickle.dump(mru_layouts, open(mru_file, 'w'))
        return ret
    if NO_END:
        lock_and_com_file = os.path.join(lltmpdir, '%s' %
                session)
        f = open(lock_and_com_file, 'w')
        f.write(str(os.getpid()) + '\n')
        if requirecleanup_win and not requirecleanup_lay:
            f.write(wnum + '\n')
        else:
            f.write('-1\n')
        if requirecleanup_lay:
            f.write(lnum + '\n')
        else:
            f.write('-1\n')
        f.close()

    try:
        try:
            layinfo = list(sc.gen_layout_info(ss, sc.dumpscreen_layout_info(ss)))
        finally:
            sc.cleanup()
    except:
        sys.stderr.write('Layouts dumping error.\n')
        return 1
    screen = curses.initscr()
    (laytable, pos_start) = create_table(ss, screen, curlay, layinfo,
            lnum, height)
    try:
        curses.start_color()
    except:
        curses.endwin()
        sys.stderr.write('start_color() failed!\n')
        return 1

    curses.noecho()

    #screen.notimeout(1)

    try:
        choice = menu_table(
            ss,
            screen,
            lnum,
            curwin,
            curlay,
            layinfo,
            laytable,
            pos_start[0],
            pos_start[1],
            height,
            )
        if requirecleanup_lay and choice == lnum:
            choice = curlay
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        choice = curlay
        ret = 1
    curses.endwin()
    if NO_END:
        from util import remove
        remove(lock_and_com_file)
    if requirecleanup_lay:
        ss.command_at(False,
                      'eval "layout select %s" "layout remove %s" "at \"%s\#\" kill" "layout title"' %
                      (choice, lnum, wnum))
    elif requirecleanup_win:
        ss.command_at(False,
                      'eval "select %s" "layout select %s" "at \"%s\#\" kill" "layout title"' %
                      (curwin, choice, wnum))
    else:
        ss.command_at(False, 'eval "layout select %s" "layout title"' %
                      choice)
    return ret


if __name__ == '__main__':
    session = (sys.argv)[1]
    curwin = (sys.argv)[2]
    curlay = (sys.argv)[3]
    requirecleanup_win = (sys.argv)[4] == '1' and True or False
    requirecleanup_lay = (sys.argv)[5] == '1' and True or False
    NO_END = (sys.argv)[6] == '1' and True or False
    MAXTITLELEN = int((sys.argv)[7])
    AUTOSEARCH_MIN_MATCH = int((sys.argv)[8])

    try:
        height = int((sys.argv)[9])
    except:
        height = 20

    run(session, requirecleanup_win, requirecleanup_lay, curwin, curlay,
        height)

