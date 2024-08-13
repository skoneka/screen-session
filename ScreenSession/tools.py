#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    tools.py : functions used by tools
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
#             Brendon Crawford https://github.com/brendoncrawford
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

from ScreenSaver import ScreenSaver
import GNUScreen as sc
import os
from sys import stderr
from six.moves import map

dumpscreen_window = sc.dumpscreen_window
require_dumpscreen_window = sc.require_dumpscreen_window


def cleanup():
    sc.cleanup()


def find_pids_in_windows(session, datadir, pids):
    import getpass
    import os
    tty_and_pids = sc._get_tty_pids_ps_with_cache_gen(getpass.getuser())

    #print(tty_and_pids)

    ttys = []
    for (tty, tpids) in tty_and_pids.items():

        #print('%s %s %s'%(pids,tty,tpids))

        for pid in pids:
            if pid in tpids:
                ttys.append(tty)
    wins = []
    for (cwin, cgroupid, ctype, ctty, ctitle) in sc.gen_all_windows_fast(session,
            datadir):
        try:
            ctty = int(os.path.split(ctty)[1])
            if ctty in ttys:
                wins.append(tuple([cwin, ctitle]))
        except Exception:
            pass
    return wins


def find_files_in_pids(files):
    import os
    cmd = 'lsof -F p %s | cut -c2-' % (" ").join(["\"%s\"" % v for v in
            files])
    f = os.popen(cmd)
    pids = f.read().strip().split('\n')
    f.close()
    return pids


def dump(ss, datadir, showpid=True, reverse=True, sort=False, groupids=[]):
    from sys import stdout
    bShow = True
    windows = []
    sum_process_total = 0
    sum_win = 0
    sum_zombie = 0
    sum_basic = 0
    sum_group = 0
    sum_telnet = 0
    sum_primer = 0
    sum_vim = 0
    if groupids:
        (groups, windows) = subwindows(ss.pid, datadir, groupids)
    try:
        for (
            cwin,
            cgroupid,
            cgroup,
            ctty,
            ctype,
            ctypestr,
            ctitle,
            cfilter,
            cscroll,
            ctime,
            cmdargs,
            ) in sc.gen_all_windows_full(ss.pid, datadir, reverse, sort):
            if groupids:
                if cwin in windows:
                    bShow = True
                else:
                    bShow = False
            if bShow:
                sum_win += 1
                if ctype == -1:
                    sum_zombie += 1
                elif ctype == 0:
                    sum_basic += 1
                elif ctype == 1:
                    sum_group += 1
                elif ctype == 2:
                    sum_telnet += 1
                print("----------------------------------------")
                lines = []
                lines.append("%s TYPE %s\n" % (cwin, ctypestr))
                if cgroupid == "-1":
                    groupstr = "-1"
                else:
                    groupstr = cgroupid + " " + cgroup
                lines.append("%s GRP %s\n" % (cwin, groupstr))
                lines.append("%s TITL %s\n" % (cwin, ctitle))
                cmdargs = cmdargs.split('\0')
                pcmdargs = cmdargs[0]
                if cmdargs[1] != '':
                    pcmdargs += " " + (" ").join(["\"%s\"" % v for v in
                            cmdargs[1:-1]])
                lines.append("%s CARG %s\n" % (cwin, pcmdargs))
                if cfilter != "-1":
                    lines.append("%s EXEC %s\n" % (cwin, cfilter))
                if ctype == 0:
                    lines.append("%s TTY %s\n" % (cwin, ctty))
                    if showpid:
                        try:
                            pids = sc.get_tty_pids(ctty)
                            for pid in pids:
                                sum_process_total += 1
                                try:
                                    (cwd, exe, cmd) = sc.get_pid_info(pid)
                                    lines.append("%s PID %s CWD %s\n" % (cwin,
                                            pid, cwd))
                                    lines.append("%s PID %s EXE %s\n" % (cwin,
                                            pid, exe))
                                    cmd = cmd.split('\0')
                                    pcmd = cmd[0]

                                    if cmd[1] != '':
                                        pcmd += " "+" ".join(["\"%s\"" % v for v in cmd[1:-1]])

                                    lines.append("%s PID %s CMD %s\n" % (cwin,
                                            pid, pcmd))

                                    if cmd[0].endswith('screen-session-primer') and cmd[1] == '-p':
                                        sum_primer += 1
                                        lines[0] = lines[0][:-1] + " / primer\n"
                                    elif cmd[0] in ('vi', 'vim', 'viless', 'vimdiff'):
                                        sum_vim += 1
                                        lines[0] = lines[0][:-1] + " / VIM\n"
                                except OSError as x:
                                    lines.append("%s PID %s Unable to access pid data ( %s )\n" %
                                            (cwin, pid, str(x)))
                        except Exception as x:
                            lines.append("%s Unable to access PIDs associated with tty ( %s )\n" %
                                    (cwin,str(x)))
                try:
                    list(map(stdout.write, lines))
                except:
                    break

        print('WINDOWS: %d\t[ %d basic | %d group | %d zombie | %d telnet ]' % \
            (sum_win, sum_basic, sum_group, sum_zombie, sum_telnet))
        print('PROCESS: %d\t[ %d primer | %d vim ]' % (sum_process_total,
                sum_primer, sum_vim))
    except IOError:
        pass


def renumber(session, datadir):
    ss = ScreenSaver(session, '/dev/null', '/dev/null')
    wins = []
    wins_trans = {}
    for (cwin, cgroupid, ctype, ctty, ctitle) in sc.gen_all_windows_fast(session,
            datadir):
        iwin = int(cwin)
        wins.append((iwin, cgroupid, ctype))
        wins_trans[iwin] = iwin

    wins.sort(key=lambda wins: wins[0])
    print(wins_trans)
    i = 0
    for (win, groupid, ctype) in wins:
        if wins_trans[win] != i:

            #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))

            ss.number(str(i), str(wins_trans[win]))
            tmp = wins_trans[win]
            try:
                wins_trans[win] = wins_trans[i]
            except:
                wins_trans[win] = -1
            wins_trans[i] = tmp
        i += 1
    print(wins_trans)


def sort(session, datadir, key=None):
    ss = ScreenSaver(session, '/dev/null', '/dev/null')
    wins = []
    wins_trans = {}
    groups = {}
    cgroup = None
    for (cwin, cgroupid, ctype, ctty, ctitle) in sc.gen_all_windows_fast(session,
            datadir):
        iwin = int(cwin)
        lastval = (groupid, iwin, ctype, ss.title('', iwin))
        try:
            groups[groupid].append(lastval)
        except:
            groups[groupid] = [lastval]
        wins_trans[iwin] = iwin

    i = 0
    for (group, props) in groups.items():
        try:
            props.sort(key=lambda wins: wins[3].lower())
        except:
            print('FAIL')
            print(str(len(props)) + ' : ' + group + ' : ' + str(props))
            pass

        #print( str(len(props))+' : '+group + ' : ' + str(props))

        for (groupid, win, ctype, title) in props:
            if wins_trans[win] != i:

                #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))

                ss.number(str(i), str(wins_trans[win]))
                tmp = wins_trans[win]
                try:
                    wins_trans[win] = wins_trans[i]
                except:
                    wins_trans[win] = -1
                wins_trans[i] = tmp
            i += 1
    return


def kill_zombie(session, datadir, groupids=[]):
    ss = ScreenSaver(session, '/dev/null', '/dev/null')
    if groupids:
        windows = subwindows(session, datadir, groupids)[1]
    for (cwin, cgroupid, ctype, ctty, ctitle) in sc.gen_all_windows_fast(session,
            datadir):
        if ctype == -1:
            if groupids:
                if cwin in windows:
                    ss.kill(cwin)
            else:
                ss.kill(cwin)


def subwindows(session, datadir, groupids):
    ss = ScreenSaver(session)
    bAll = False
    try:
        if groupids[0] in ('cg', 'current', '..'):
            groupids[0] = ss.get_group()[0]
            if groupids[0] == "-1":
                bAll = True
        elif groupids[0] in ('cw', 'current-window', '.'):
            groupids[0] = ss.get_number_and_title()[0]
        elif groupids[0] == 'all':
            bAll = True
    except IndexError:
        bAll = True
    group_wins = {}
    group_groups = {}
    excluded_wins = []
    excluded_groups = []
    for (cwin, cgroupid, ctype, ctty, ctitle) in sc.gen_all_windows_fast(session,
            datadir):
        if ctype == 1:  # group
            if cwin in groupids or bAll or ctitle in groupids:
                excluded_groups.append(cwin)
            try:
                group_groups[cgroupid] += [cwin]
            except:
                group_groups[cgroupid] = [cwin]
        else:

              # anything other than group

            if cwin in groupids or bAll or ctitle in groupids:
                excluded_wins.append(cwin)
            else:
                try:
                    group_wins[cgroupid] += [cwin]
                except:
                    group_wins[cgroupid] = [cwin]
    excluded_groups_tmp = []
    while excluded_groups:
        egroup = excluded_groups.pop()
        if egroup not in excluded_groups_tmp:
            excluded_groups_tmp.append(egroup)
        try:
            ngroups = group_groups[egroup]
            if ngroups:
                for g in ngroups:
                    excluded_groups.append(g)
        except:
            pass
    excluded_groups = excluded_groups_tmp
    for egroup in excluded_groups:
        excluded_wins.append(egroup)
        try:
            for w in group_wins[egroup]:
                excluded_wins.append(w)
        except:
            pass
    return (excluded_groups, excluded_wins)


def kill_group(session, datadir, groupids):
    ss = ScreenSaver(session)
    (excluded_groups, excluded_wins) = subwindows(session, datadir,
            groupids)
    print('Killing groups: %s' % str(excluded_groups))
    print('All killed windows: %s' % str(excluded_wins))

    for win in excluded_wins:
        ss.kill(win)

    ## sourcing commands may lock Screen session 
    #from util import tmpdir_source, remove
    #if not os.path.exists(tmpdir_source):
    #    os.makedirs(tmpdir_source)
    #sourcefile = os.path.join(tmpdir_source, 'kill_group-%d' % os.getpid())
    #f = open(sourcefile, 'w')
    #
    #for win in excluded_wins:
    #    f.write('at %s kill\n' % win)
    #
    #f.close()
    #ss.source(sourcefile)
    ##remove(sourcefile)


def get_win_last_proc(session, win="-1", ctty = None):
    import platform
    if not ctty:
        ss = ScreenSaver(session, '/dev/null', '/dev/null')
        ctty = ss.tty(win)
    if ctty is None or ctty == -1:
        stderr.write("Window does not exist (%s)\n" % win)
        return False
    if platform.system() == 'FreeBSD':
        pids = sc.get_tty_pids(ctty)
    else:
        pids = sc._get_tty_pids_pgrep(ctty)
    if len(pids) > 0:
        return pids[-1]
    else:

        ## No processes for this window.

        return None


def kill_win_last_proc(session, win="-1", sig="TERM", ctty = None):
    import signal
    pid = get_win_last_proc(session, win, ctty)
    if pid:
        snum = 'SIG' + sig.upper()
        if hasattr(signal, snum):
            siggy = getattr(signal, snum)
            try:
                os.kill(int(pid), siggy)
            except OSError:
                stderr.write("Invalid process\n")
                return False
            else:
                return True
        else:
            stderr.write("Not a valid signal (%s)\n" % sig)
            return False
    else:

        ## No processes for this window.
        ## Do nothing

        return False


