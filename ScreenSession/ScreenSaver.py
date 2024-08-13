#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    ScreenSaver.py : a class which saves and loads sessions, it also contains
#                     many important functions interfacing with GNU Screen
#                     ( which should be moved to GNUScreen.py )
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

import sys
import os
import pwd
import getopt
import glob
import time
import signal
import shutil
import tempfile
import traceback
import re
import linecache
import datetime

from util import out, requireme, linkify, which, timeout_command
import util
import GNUScreen as sc
from GNUScreen import SCREEN
from six.moves import map
from six.moves import range


class ScreenSaver(object):

    """class for storing GNU screen sessions"""

    timeout = 3
    pid = ""  # actually it is the sessionname
    basedir = ""
    projectsdir = ".screen-sessions"
    savedir = ""
    force = False
    enable_layout = False
    exact = False
    bVim = True
    bShellvars = True
    mru = True
    bNoGroupWrap = False
    force_start = []
    scroll = []
    group_other = 'OTHER_WINDOWS'
    homewindow = ""
    sc = None
    wrap_group_id = None
    none_group = 'none_NoSuChGrOuP'

    primer_base = "screen-session-primer"
    primer = primer_base
    primer_arg = "-p"

    # blacklist file in projects directory

    blacklistfile = "BLACKLIST"

    # old static blacklist

    blacklist = ("rm", "shutdown")

    # user's list of excluded windows and layouts

    excluded = None
    excluded_layouts = None

    vim_names = ('vi', 'vim', 'viless', 'vimdiff')
    shell_names = ('bash')

    __unique_ident = None
    __wins_trans = {}
    __scrollbacks = []
    __layouts_loaded = False
    __vim_files = []  # a list of vim savefiles, wait for them a few seconds, otherwise continue

    def __init__(self, pid, projectsdir='/dev/null', savedir='/dev/null'):
        self.homedir = os.path.expanduser('~')
        self.projectsdir = str(projectsdir)
        self.basedir = os.path.join(self.homedir, self.projectsdir)
        self.savedir = str(savedir)
        self.pid = str(pid)
        self.set_session(self.pid)
        self.primer = os.path.join(os.path.dirname((sys.argv)[0]), self.primer)
        self._scrollfile = os.path.join(self.savedir, "hardcopy.")

    def set_session(self, sessionname):
        self.sc = '%s -S \"%s\"' % (SCREEN, sessionname)
        self.__unique_ident = "S%s_%s" % (sessionname.split('.', 1)[0],
                time.strftime("%d%b%y_%H-%M-%S"))

    def save(self):
        (self.homewindow, title) = self.get_number_and_title()
        out("\nCreating directories:")
        if not self.__setup_savedir(self.basedir, self.savedir):
            return 1
        sc.require_dumpscreen_window(self.pid, True)

        if self.enable_layout:
            out("\nSaving layouts:")
            self.__save_layouts()

        out("\nSaving windows:")
        self.__save_screen()

        out("\nCleaning up scrollbacks.")
        self.__scrollback_clean()
        if self.__vim_files:
            self.__wait_vim()
        return 0

    def load(self):
        if 'all' in self.force_start:
            self.primer_arg += 'S'
            self.force_start = []
        if 'all' in self.scroll:
            self._scrollfile = None
        out('session "%s" loading "%s"' % (self.pid, os.path.join(self.basedir,
            self.savedir)))

        #check if the saved session exists and get the biggest saved window number and a number of saved windows

        maxnewwindow = 0
        newwindows = 0
        try:
            winlist = list(glob.glob(os.path.join(self.basedir, self.savedir,
                           'win_*')))
            newwindows = len(winlist)
            out('%d new windows' % newwindows)
        except Exception:
            sys.stderr.write('Unable to open winlist.\n')
            return 1

        # keep original numbering, move existing windows

        self.homewindow = self.number()

        if self.exact:
            maxnewwindow = -1
            for w in winlist:
                try:
                    w = int(w.rsplit("_", 1)[1])
                    if w > maxnewwindow:
                        maxnewwindow = w
                except:
                    pass

            out('Biggest new window number: %d' % maxnewwindow)
            if self.enable_layout:
                self.__remove_all_layouts()
            self.__move_all_windows(maxnewwindow + 1, self.group_other,
                                    False)

        out("\nLoading windows:")
        self.__load_screen()

        if self.enable_layout:
            out("\nLoading layouts:")
            try:
                self.__load_layouts()
            except:
                sys.stderr.write('Layouts loading failed!\n')
                # raise

        self.__restore_mru()
        sc.cleanup()

        return 0

    def exists(self):
        msg = self.echo('test')
        try:
            if msg.startswith('No'):  # 'No screen session found'
                return False
            else:
                return True
        except:
            return False

    def __escape_bad_chars(self, str):

        # some characters are causing problems when setting window titles with screen -t "title"

        return str.replace('|', 'I').replace('\\', '\\\\\\\\').replace('"',
                '\\"')  # how to properly escape "|" in 'screen -t "part1 | part2" sh'?

    def __restore_mru(self):
        if self.enable_layout and not self.mru:
            pass
        else:
            try:
                if self.mru:
                    sys.stdout.write("\nRestoring MRU windows order:")
                else:
                    sys.stdout.write("\nSelecting last window:")

                mru_w = []
                ifmru = open(os.path.join(self.basedir, self.savedir,
                             "mru"), 'r')
                for line in ifmru:
                    n = line.strip()
                    try:
                        nw = (self.__wins_trans)[n]
                        mru_w.append('select ' + nw + '\n')
                        sys.stdout.write(' %s' % nw)
                        if not self.mru:
                            break
                    except:
                        if self.enable_layout:
                            mru_w.append('select -\n')
                        else:
                            pass
                ifmru.close()
                mru_w.reverse()
                path_mru_tmp = os.path.join(self.basedir, self.savedir,
                        "mru_tmp")
                ofmru = open(path_mru_tmp, "w")
                ofmru.writelines(mru_w)
                ofmru.close()
                self.source(path_mru_tmp)
                util.remove(path_mru_tmp)
            except:
                sys.stderr.write(' Failed to load MRU.')
            out("")

    def __load_screen(self):
        homewindow = self.homewindow

        # out ("Homewindow is " +homewindow)

        #check if target Screen is currently in some group and set hostgroup to it

        (hostgroupid, hostgroup) = self.get_group(homewindow)
        rootwindow = self.number()
        if self.exact:
            rootgroup = self.none_group
            hostgroup = self.none_group
        elif self.bNoGroupWrap:
            rootgroup = self.none_group
        else:

            #create a root group and put it into host group

            rootgroup = "RESTORE_" + self.savedir
            rootwindow = self.screen('-t \"%s\" %s //group' % (rootgroup, 0))
            self.group(False, hostgroup, rootwindow)

        out("restoring Screen session inside window %s (%s)" % (rootwindow,
            rootgroup))

        self.command_at(True, 'setenv SCREENSESSION %s' % os.path.join(self.basedir, self.savedir) )

        wins = []
        savedir_path = os.path.join(self.basedir, self.savedir)

        for filename in os.listdir(savedir_path):
            if filename.startswith("win_") and filename[4:].isdigit():
                try:
                    file_path = os.path.join(savedir_path, filename)
                    with open(file_path, 'r') as f:
                        win = [line.strip() for line in f.readlines()[:9]]

                    nproc = win[8] if len(win) > 8 else '0'

                    wins.append((
                        win[0],
                        win[1],
                        win[2],
                        win[3],
                        self.__escape_bad_chars(win[4]),
                        win[5],
                        win[6],
                        win[7],
                        nproc,
                    ))
                except Exception as x:
                    id = filename[4:]  # Extract the id from the filename
                    sys.stderr.write('%d Unable to load window ( %s )\n' %
                        (id, str(x)))

        try:
            for (
                win,
                time,
                group,
                type,
                title,
                filter,
                scrollback_len,
                cmdargs,
                processes,
                ) in wins:
                (self.__wins_trans)[win] = self.__create_win(
                    self.exact,
                    self.__wins_trans,
                    self.pid,
                    hostgroup,
                    rootgroup,
                    win,
                    time,
                    group,
                    type,
                    title,
                    filter,
                    scrollback_len,
                    cmdargs,
                    processes,
                    )
        except ValueError:
            sys.stderr.write('Ignoring windows - maximum number of windows reached.\n')

        for (
            win,
            time,
            group,
            type,
            title,
            filter,
            scrollback_len,
            cmdargs,
            processes,
            ) in wins:
            try:
                try:
                    (groupid, group) = group.split(" ", 1)
                except:
                    groupid = "-1"
                    group = self.none_group
                self.__order_group(
                    (self.__wins_trans)[win],
                    self.pid,
                    hostgroup,
                    rootwindow,
                    rootgroup,
                    win,
                    time,
                    groupid,
                    group,
                    type,
                    title,
                    filter,
                    scrollback_len,
                    processes,
                    )
            except:
                pass

        out("Rootwindow is " + rootwindow)
        if self.wrap_group_id:
            out("Wrap group is " + self.wrap_group_id)
        self.select(rootwindow)

    def __create_win(
        self,
        keep_numbering,
        wins_trans,
        pid,
        hostgroup,
        rootgroup,
        win,
        time,
        group,
        type,
        title,
        filter,
        scrollback_len,
        cmdargs,
        processes,
        ):
        if keep_numbering:
            winarg = win
        else:
            winarg = ""

        if type[0] == 'b' or type[0] == 'z':
            if win in self.force_start:
                primer_arg = self.primer_arg + 'S'
            else:
                primer_arg = self.primer_arg
            if win in self.scroll or not self._scrollfile or not os.path.exists(os.path.join(self.homedir,
                    self.projectsdir, self._scrollfile + win)):
                scrollfile = '0'
            else:
                scrollfile = self._scrollfile + win

            #print ('-h %s -t \"%s\" %s %s %s %s %s %s' % (scrollback_len,title,winarg,self.primer,primer_arg,self.projectsdir, scrollfile,os.path.join(self.savedir,"win_"+win)))

            newwin = self.screen('-h %s -t \"%s\" %s "%s" "%s" "%s" "%s" "%s"' %
                        (scrollback_len, title, winarg, self.primer,
                        primer_arg, self.projectsdir, scrollfile, os.path.join(self.savedir,
                        "win_" + win)))
        elif type[0] == 'g':

            #self.screen('-h %s -t \"%s\" %s %s %s %s %s %s' % (scrollback_len,title,winarg,self.primer,primer_arg,self.projectsdir,"0",os.path.join(self.savedir,"win_"+win)) )

            newwin = self.screen('-t \"%s\" %s //group' % (title, winarg))
        else:
            sys.stderr.write('%s Unknown window type "%s". Ignoring.\n' % (win, type))
            return -1

        return newwin

    def __order_group(
        self,
        newwin,
        pid,
        hostgroup,
        rootwindow,
        rootgroup,
        win,
        time,
        groupid,
        group,
        type,
        title,
        filter,
        scrollback_len,
        processes,
        ):
        if groupid == "-1":

            # this select is necessary in case of a group name conflict

            self.select(rootwindow)
            self.group(False, rootgroup, newwin)
        else:
            try:
                groupid = (self.__wins_trans)[groupid]
            except:
                pass

            # this select is necessary in case of a group name conflict

            self.select(groupid)
            self.group(False, group, newwin)

    def __scrollback_clean(self):
        """clean up scrollback files: remove empty lines at the beginning and at the end of a file"""

        for f in glob.glob(os.path.join(self.basedir, self.savedir,
                           "hardcopy.*")):
            try:
                ftmp = f + "_tmp"
                temp = open(ftmp, "w")
                thefile = open(f, 'r')
                beginning = True
                for line in thefile:
                    if beginning:
                        if cmp(line, '\n') == 0:
                            line = line.replace('\n', "")
                        else:
                            beginning = False
                    temp.write(line)
                temp.close()
                thefile.close()

                temp = open(ftmp, 'r')
                endmark = -1
                lockmark = False
                for (i, line) in enumerate(temp):
                    if cmp(line, '\n') == 0:
                        if not lockmark:
                            endmark = i
                            lockmark = True
                    else:
                        endmark = -1
                        lockmark = False
                temp.close()

                if endmark > 1:
                    thefile = open(f, "w")
                    temp = open(ftmp, 'r')
                    for (i, line) in enumerate(temp):
                        if i == endmark:
                            break
                            None
                        else:
                            thefile.write(line)
                    thefile.close()
                    temp.close()
                    util.remove(ftmp)
                else:
                    util.remove(f)
                    os.rename(ftmp, f)
            except:
                sys.stderr.write('Unable to clean scrollback file: ' + f + '\n')

    def __remove_all_layouts(self):
        currentlayout = 0
        while currentlayout != -1:
            self.layout('remove', False)
            self.layout('next', False)
            (currentlayout, currentlayoutname) = self.get_layout_number()

    def __move_all_windows(self, shift, group, kill=False):
        homewindow = int(self.homewindow)

        # create a wrap group for existing windows

        if not self.bNoGroupWrap:
            self.wrap_group_id = self.screen('-t \"%s\" //group' % ('%s_%s' % (group, self.__unique_ident)))
            self.group(False, self.none_group, self.wrap_group_id)

        # move windows by shift and put them in a wrap group
        #for cwin,cgroupid,ctype,ctty in sc.gen_all_windows_fast(self.pid):

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
            ) in sc.gen_all_windows_full(self.pid, sc.require_dumpscreen_window(self.pid,
                    True)):
            iwin = int(cwin)
            if iwin == homewindow:
                homewindow = iwin + shift
                self.homewindow = str(homewindow)

            if not self.bNoGroupWrap and cgroup == self.none_group:
                self.select(self.wrap_group_id)
                self.group(False, group, str(cwin))
            command = '%s -p %s -X number +%d' % (self.sc, cwin, shift)
            if not self.bNoGroupWrap and str(cwin) == str(self.wrap_group_id):
                out('Moving wrap group %s to %d' % (cwin, iwin + shift))
                self.wrap_group_id = str(iwin + shift)
            else:
                out('Moving window %s to %d' % (cwin, iwin + shift))
            os.system(command)
        self.select('%d' % homewindow)

    def lastmsg(self):
        return util.timeout_command('%s -Q @lastmsg' % self.sc, self.timeout)[0]

    def command_at(self, output, command, win="-1"):
        if win == "-1":
            swin = ""
        else:
            swin = "-p %s" % win
        cmd = r"""%s %s -X %s""" % (self.sc, swin, command)

        # print ('command_at(%s, %s, %s): %s'%(output, command, win, cmd))

        os.system(cmd)
        if output:
            l = self.lastmsg()
            # print ('>>> %s' % l)
            if not l:
                return ""
            if l.startswith('C'):

                #no such window

                return -1
            else:
                return l

    def query_at(self, command, win="-1"):
        if win == "-1":
            win = ""
        else:
            win = r'''-p "%s"''' % win
        try:
            cmd = r"""%s %s -Q @%s""" % (self.sc, win, command)
            l = util.timeout_command(cmd, self.timeout)[0]

            # print ('%s = query_at(%s, %s): %s'%(l, command, win , cmd))

            if l.startswith('C'):

                #no such window

                return -1
            else:
                return l
        except:
            return None

    def get_number_and_title(self, win="-"):
        msg = self.query_at('number', win)
        (number, title) = msg.split("(", 1)
        number = number.strip()
        title = title.rsplit(")", 1)[0]
        return (number, title)

    def get_sessionname(self):
        return self.command_at(True, 'number', win).strip('\'').split('\'',
                1)[1]

    def tty(self, win="-1"):
        msg = self.query_at('tty', win)
        return msg

    '''
    def get_info(self,win):

        msg=self.command_at(True, 'info',win)
        return msg
    '''

    def info(self, win="-1"):
        msg = self.query_at('info', win)
        if msg != -1:
            r = []
            (head, tail) = msg.split(" ", 1)
            (size1, size2) = head.split('/')
            (size2, size3) = size2.split(")")
            (size1x, size1y) = size1.strip('()').split(',')
            (size2x, size2y) = size2.strip('()').split(',')
            (flow, encoding, number_title) = tail.strip().split(" ", 2)
            (number, title) = number_title.split("(", 1)
            title.strip(")")
            return (
                size1x,
                size1y,
                size2x,
                size2y,
                size3,
                flow,
                encoding,
                number,
                title,
                )
        else:
            return None

    def dinfo(self):
        msg = self.command_at(True, 'dinfo')
        msg = msg.split(" ")
        nmsg = msg.pop(0).strip("(").rstrip(")").split(',', 1)
        nmsg = nmsg + msg
        return nmsg

    def echo(self, args, win="-1"):
        msg = self.query_at('echo \"%s\"' % args, win)
        return msg

    def Xecho(self, args, win="-1"):
        msg = self.command_at(False, 'echo \"%s\"' % args)

    def number(self, args="", win="-"):
        msg = self.query_at('number %s' % args, win)
        if not args:
            return msg.split(" (", 1)[0]

    def focusminsize(self, args=""):
        msg = self.command_at(args and True or False, 'focusminsize %s' % args)
        if args:
            try:
                return msg.split('is ', 1)[1].strip()
            except:
                return '0 0'

    def stuff(self, args="", win="-"):
        self.command_at(False, 'stuff "%s"' % args, win)

    def colon(self, args="", win="-"):
        self.command_at(False, 'colon "%s"' % args, win)

    def resize(self, args=""):
        self.command_at(False, 'resize %s' % args)

    def focus(self, args=""):
        self.command_at(False, 'focus %s' % args)

    def kill(self, win="-"):
        self.command_at(False, 'kill', win)

    def idle(self, timeout, args):
        self.command_at(False, 'idle %s %s' % (timeout, args))

    def only(self):
        self.command_at(False, 'only')

    def quit(self):
        self.command_at(False, 'quit')

    def fit(self):
        self.command_at(False, 'fit')

    def layout(self, args="", output=True):
        msg = self.command_at(output, 'layout %s' % args)
        return msg

    def split(self, args=""):
        self.command_at(False, 'split %s' % args)

    def screen(self, args="", win="-"):
        msg = self.query_at('screen %s' % args, win)
        if msg.startswith('No more'):
            raise ValueError('No more windows.')
        else:
            return msg.split(':')[1].strip()
    def scrollback(self, args="", win="-"):
        msg = self.command_at(True, 'scrollback %s' % args, win)
        return msg.rsplit(" ", 1)[1].strip()

    def source(self, args="", msg=None):
        f = None
        start = datetime.datetime.now()
        while f == None:
            try:
                f = open(args, 'r')
            except:
                now = datetime.datetime.now()
                if (now - start).seconds > 2:
                    raise IOError
        f.close()
        self.command_at(False, "source \"%s\"" % args)
        if not msg:
            msg = "sourcing %s" % args
        self.command_at(False, "echo \"%s\"" % msg)  # this line seems to force Screen to read entire sourced file, so it can be deleted afterwards

    def select(self, args="", win="-"):
        msg = self.query_at('select %s' % args, win)
        return msg

    def sessionname(self, args=""):
        if len(args) > 0:
            name = self.command_at(True, 'sessionname').rsplit('\'', 1)[0].split('\'',
                    1)[1]
            nsessionname = "%s.%s" % (name.split('.', 1)[0], args)
        else:
            nsessionname = None
        msg = self.command_at(True, 'sessionname %s' % args)
        if nsessionname:
            self.pid = nsessionname
            self.set_session(self.pid)
            return nsessionname
        else:
            try:
                return msg.rsplit('\'', 1)[0].split('\'', 1)[1]
            except:
                return None

    def time(self, args=""):
        if args:
            args = '"%s"' % args
        msg = self.query_at('time %s' % args)
        return msg

    def title(self, args="", win="-"):
        if args:
            args = '"%s"' % args
            self.command_at(False, 'title %s' % args, win)
        else:
            msg = self.query_at('title', win)
            return msg

    def windows(self):
        msg = self.query_at('windows')
        return msg

    def wipe(self, args=""):
        os.popen(SCREEN + ' -wipe %s' % args)

    def backtick(self, id, lifespan="", autorefresh="", args=""):
        self.command_at(False, 'backtick %s %s %s %s' % (id, lifespan,
                        autorefresh, args))

    def get_layout_number(self):
        msg = self.command_at(True, 'layout number')
        if not msg.startswith('This is layout'):
            return (-1, -1)
        (currentlayout, currentlayoutname) = msg.split('layout', 1)[1].split("(",
                1)
        currentlayout = currentlayout.strip()
        currentlayoutname = currentlayoutname.rsplit(")", 1)[0]
        return (currentlayout, currentlayoutname)

    def get_layout_new(self, name=""):
        msg = self.command_at(True, 'layout new \'%s\'' % name)
        if msg.startswith('No more'):
            return False
        else:
            return True

    def get_group(self, win="-"):
        msg = self.query_at('group', win)
        if msg.endswith('no group'):
            group = self.none_group
            groupid = "-1"
        else:
            (groupid, group) = msg.rsplit(")", 1)[0].split(" (", 1)
            groupid = groupid.rsplit(" ", 1)[1]
        return (groupid, group)

    def group(self, output=True, args="", win="-"):
        if args:
            args = '"%s"' % args
        msg = self.command_at(output, 'group %s' % args, win)
        if output:
            if msg.endswith('no group'):
                group = self.none_group
                groupid = "-1"
            else:
                (groupid, group) = msg.rsplit(")", 1)[0].split(" (", 1)
                groupid = groupid.rsplit(" ", 1)[1]
            return (groupid, group)

    def get_exec(self, win):
        msg = self.command_at(True, 'exec', win)
        msg = msg.split(':', 1)[1].strip()
        if msg.startswith('(none)'):
            return -1
        else:
            return msg

    def __save_screen(self):
        errors = []
        homewindow = self.homewindow
        group_wins = {}
        group_groups = {}
        excluded_wins = []
        excluded_groups = []
        scroll_wins = []
        scroll_groups = []
        cwin = -1
        ctty = None
        cppids = {}
        rollback = (None, None, None)
        ctime = self.time()
        findir = sc.datadir
        os.symlink(os.path.join(findir), os.path.join(self.basedir, self.savedir))

        #sc_cwd=self.command_at(True,'hardcopydir') # it only works interactively
        # should be modified to properly restore hardcopydir(:dumpscreen settings)

        self.command_at(False,
                        'eval \'hardcopydir \"%s\"\' \'at \"\#\" hardcopy -h\' \'hardcopydir \"%s\"\'' %
                        (findir, self.homedir))
        mru_w = [homewindow + '\n']
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
            badctime,
            cmdargs,
            ) in sc.gen_all_windows_full(self.pid, sc.datadir, False,
                    False):
            mru_w.append("%s\n" % cwin)

            cpids = None
            cpids_data = None

            if ctypestr[0] == 'g':
                pass
            elif ctypestr[0] == 'z':
                cpids = []
            else:
                # get sorted pids associated with the window

                try:
                    cpids = sc.get_tty_pids(ctty)
                    cpids_data = []
                    ncpids = []
                    for pid in cpids:
                        try:
                            pidinfo = sc.get_pid_info(pid)
                            (exehead, exetail) = os.path.split(pidinfo[1])
                            if exetail in self.blacklist:
                                blacklist = True
                            else:
                                blacklist = False
                            cpids_data.append(pidinfo + tuple([blacklist]))
                            ncpids.append(pid)
                        except Exception as x:
                            if cwin != homewindow:
                                errors.append('%s PID %s: Unable to access ( %s )' %
                                    (cwin, pid, str(x)))
                    cpids = ncpids
                except Exception as x:
                    errors.append('%s Unable to access %s ( %s )' %
                            (cwin, str(ctty), str(x)))
                    cpids=[]

            if cpids:
                for (i, pid) in enumerate(cpids):
                    if cpids_data[i][3]:
                        text = "BLACKLISTED"
                    else:
                        text = ""
                    l = cpids_data[i][2].split('\x00')
                    jremove = []
                    wprev = False
                    for (j, w) in enumerate(l):
                        if w == '-ic' or w == '-c':
                            wprev = True
                        elif wprev:
                            if w.startswith(self.primer):
                                jremove += (j, j - 1)
                            wprev = False
                    if jremove:
                        s = []
                        for (j, w) in enumerate(l):
                            if j not in jremove:
                                s.append(w)
                        newdata = (cpids_data[i][0], cpids_data[i][1], ('\x00').join(["%s" %
                                   v for v in s]), cpids_data[i][3])
                        cpids_data[i] = newdata

                    #out('%s    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (text,pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))

                    extra_data_name = str(None)
                    args = cpids_data[i][2].split('\x00')
                    if args[0].endswith(self.primer_base) and args[1] == \
                        "-p":
                        sys.stdout.write('(primer)')
                        rollback = self.__rollback(cpids_data[i][2])
                    elif args[0] in self.vim_names and self.bVim and i == len(cpids_data)-1:

                        #out(str(rollback))

                        sys.stdout.write('(vim)')
                        extra_data_name = self.__save_vim(cwin)
                        nargs = []
                        rmarg = False
                        for arg in args:
                            if rmarg:
                                rmarg = False
                                pass
                            elif arg in ('-S', '-i'):
                                rmarg = True
                            else:
                                nargs.append(arg)
                        args = nargs
                        newdata = (cpids_data[i][0], cpids_data[i][1], ('\x00').join(["%s" %
                                   v for v in args]), cpids_data[i][3])
                        cpids_data[i] = newdata
                    elif self.bShellvars and args[0].split('/')[-1] in self.shell_names and i == len(cpids_data)-1:
                        sys.stdout.write('(shell)')
                        extra_data_name = self.__save_shellvars(cwin, args[0].split('/')[-1])

                    cpids_data[i] = (cpids_data[i][0], cpids_data[i][1],
                            cpids_data[i][2], cpids_data[i][3], extra_data_name)

            scrollback_filename = os.path.join(findir, "hardcopy." +
                    cwin)
            sys.stdout.write("%s %s; " % (cwin, ctypestr))
            errors += self.__save_win(cwin, ctypestr, cpids_data, ctime,
                    rollback)
            rollback = (None, None, None)
        out("")

        # remove ignored scrollbacks

        if 'all' in self.scroll:
            for f in glob.glob(os.path.join(findir, "hardcopy.*")):
                open(f, "w")
        elif self.scroll:
            import tools
            (scroll_groups, scroll_wins) = tools.subwindows(self.pid, sc.datadir,
                    self.scroll)
            out('Scrollback excluded groups: %s' % str(scroll_groups))
            out('All scrollback excluded windows: %s' % str(scroll_wins))
            for w in scroll_wins:
                util.remove(os.path.join(findir, "hardcopy.%s" % w))

        # remove ignored windows

        if self.excluded:
            import tools
            (excluded_groups, excluded_wins) = tools.subwindows(self.pid,
                    sc.datadir, self.excluded)
            out('Excluded groups: %s' % str(excluded_groups))
            out('All excluded windows: %s' % str(excluded_wins))
            bpath1 = os.path.join(findir, "win_")
            bpath2 = os.path.join(findir, "hardcopy.")
            bpath3 = os.path.join(findir, "vim_W")
            bpath4 = os.path.join(findir, "shellvars_W")
            for win in excluded_wins:
                util.remove(bpath1 + win)
                util.remove(bpath2 + win)
                for f in glob.glob(bpath3 + win + '_*'):
                    util.remove(f)
                for f in glob.glob(bpath4 + win + '_*'):
                    util.remove(f)

        #if mru_w[0] in excluded_wins or mru_w[0] in excluded_groups:
        #    mru_w[0]='-'
        #mru_w.reverse()

        fmru = open(os.path.join(findir, "mru"), "w")
        fmru.writelines(mru_w)
        fmru.close()

        if errors:
            sys.stderr.write('Errors during windows saving:\n')
            for error in errors:
                sys.stderr.write(error+'\n')
        out('\nSaved: ' + str(ctime))

    def __rollback(self, cmdline):
        try:
            cmdline = cmdline.split('\x00')
            if cmdline[3] == '0':
                requireme(self.homedir, cmdline[2], cmdline[4])
            else:
                requireme(self.homedir, cmdline[2], cmdline[3])
            path = os.path.join(self.homedir, cmdline[2], cmdline[4])
            (fhead, ftail) = os.path.split(cmdline[4])
            target = os.path.join(self.homedir, self.projectsdir, self.savedir,
                                  ftail + '__rollback')
            number = ftail.split("_")[1]
            oldsavedir = fhead

            # import win_* files from previous savefiles

            try:
                shutil.move(os.path.join(self.homedir, cmdline[2],
                            cmdline[4]), target)
            except Exception:
                target = None
                pass

            # import hardcopy.* files from previous savefiles

            (fhead, ftail) = os.path.split(cmdline[3])
            target2 = os.path.join(self.homedir, self.projectsdir, self.savedir,
                                   ftail + '__rollback')
            try:
                shutil.move(os.path.join(self.homedir, cmdline[2],
                            cmdline[3]), target2)
            except Exception:
                target2 = None
                pass

            if os.path.isfile(target):

                # fhead is savefile base name

                return (target, target2, os.path.join(self.homedir,
                        cmdline[2], fhead))
            else:
                return (None, None, None)
        except:
            return (None, None, None)

    def __load_layouts(self):
        cdinfo = list(map(int, self.dinfo()[0:2]))
        out('Terminal size: %s %s' % (cdinfo[0], cdinfo[1]))
        homewindow = self.homewindow
        (homelayout, homelayoutname) = self.get_layout_number()
        layout_trans = {}
        layout_c = len(glob.glob(os.path.join(self.basedir, self.savedir,
                       'winlayout_*')))
        if layout_c > 0:
            self.__layouts_loaded = True
        lc = 0
        layout_file = sc.layout_begin(self.pid)
        while lc < layout_c:
            filename = None
            try:
                filename = glob.glob(os.path.join(self.basedir, self.savedir,
                        'layout_%d' % lc))[0]
                layoutnumber = filename.rsplit("_", 1)[1]
                (head, tail) = os.path.split(filename)

                # the winlayout_NUM files contain "dumpscreen layout" output 
                # (see GNUScreen.Regions class)

                filename2 = os.path.join(head, "win" + tail)
                regions = sc.get_regions(filename2)
                status = self.get_layout_new(regions.title)
                if not status:
                    sys.stderr.write('\nMaximum number of layouts reached. Ignoring layout %s (%s).\n' %
                        (layoutnumber, regions.title))
                    break
                else:
                    if self.exact:
                        self.layout('number %s' % layoutnumber, False)
                        currentlayout = layoutnumber
                    else:
                        currentlayout = self.get_layout_number()[0]
                    layout_trans[layoutnumber] = currentlayout

                    sc.layout_select_layout(currentlayout)
                    # source the output produced by "layout dump"
                    sc.layout_load_dump(open(filename,'r'))

                    regions_size = []
                    winlist = []

                    for (window, sizex, sizey) in regions.regions:
                        winlist.append(window)
                        regions_size.append((sizex, sizey))
                    sc.layout_load_regions(regions, self.__wins_trans, cdinfo[0], cdinfo[1])
                    # sys.stdout.write(" %s (%s);" % (layoutnumber, regions.title))
            except:
                # import traceback
                # traceback.print_exc(file=sys.stderr)
                # raise
                layout_c += 1
                if layout_c > 2000:
                    sys.stderr.write('\nErrors during layouts loading.\n')
                    break
            lc += 1
        out('')
        if not lc == 0:

            # select last layout

            lastname = None
            lastid_l = None

            if homelayout != -1:
                out("Returning homelayout %s" % homelayout)
                layout_file.write('layout select %s' % homelayout)
            else:
                sys.stderr.write('No homelayout - unable to return.\n')

            if os.path.exists(os.path.join(self.basedir, self.savedir,
                              "last_layout")) and len(layout_trans) > 0:
                last = os.readlink(os.path.join(self.basedir, self.savedir,
                                   "last_layout"))
                (lasthead, lasttail) = os.path.split(last)
                last = lasttail.split("_", 2)
                lastid_l = last[1]
                try:
                    out("Selecting last layout: %s (%s)" % (layout_trans[lastid_l], lastid_l))
                    layout_file.write('layout select %s' % layout_trans[lastid_l])
                    # ^^ layout numbering may change, use layout_trans={}
                except:
                    sys.stderr.write("Unable to select last layout %s\n" % lastid_l)
        else:
            self.enable_layout = False
        sc.layout_end()

    def select_region(self, region):
        self.focus('top')
        for i in range(0, region):
            self.focus()

    def __save_layouts(self):
        (homelayout, homelayoutname) = self.get_layout_number()
        findir = sc.datadir
        if homelayout == -1:
            sys.stderr.write("No layouts to save.\n")
            return False
        path_layout = os.path.join(findir, "load_layout")
        oflayout = open(path_layout, "w")
        ex_lay = []
        for lay in sc.gen_layout_info(self, sc.dumpscreen_layout_info(self)):
            try:
                num = lay[0]
                title = lay[1]
            except:
                title = ""
            if self.excluded_layouts and (num in self.excluded_layouts or
                    title in self.excluded_layouts):
                ex_lay.append(lay)
            else:
                sys.stdout.write("%s(%s); " % (num, title))
                oflayout.write('''layout select %s
layout dump \"%s\"
dumpscreen layout \"%s\"
''' %
                               (num, os.path.join(findir, "layout_" +
                               num), os.path.join(findir, "winlayout_" +
                               num)))

        oflayout.write('layout select %s\n' % homelayout)
        oflayout.close()
        self.source(path_layout)
        util.remove(path_layout)
        linkify(findir, "layout_" + homelayout, "last_layout")
        if ex_lay:
            sys.stdout.write("""

Excluded layouts: %s""" % str(ex_lay))

        out("")
        return True

    def __wait_vim(self):
        sys.stdout.write('Waiting for vim savefiles... ')
        sys.stdout.flush()
        start = datetime.datetime.now()
        try:
            for fname in self.__vim_files:
                f = None
                while f == None:
                    try:
                        f = open(fname, 'r')
                        f.close()
                    except:
                        now = datetime.datetime.now()
                        if (now - start).seconds > 10:  # timeout
                            raise IOError
                        time.sleep(0.05)
            sys.stdout.write('done\n')
        except:
            sys.stdout.write('incomplete!\n')
            pass

    def __save_vim(self, winid):
        findir = sc.datadir
        name = "vim_W%s_%s" % (winid, self.__unique_ident)
        fname = os.path.join(findir, name)
        cmd = \
            """^[^[:silent call histdel(':',-1) | \
exec 'mksession' fnameescape('%s') | exec 'wviminfo' fnameescape('%s')\n""" % \
            (fname + '_session', fname + '_info')
        self.stuff(cmd, winid)
        self.__vim_files.append(fname + '_session')
        self.__vim_files.append(fname + '_info')

        # undo files become useless if the target file changes even by a single byte
        # self.stuff(":bufdo exec 'wundo! %s'.expand('%%')\n"%(fname+'_undo_'), winid)

        return name

    def __save_shellvars(self, winid, shell):
        findir = sc.datadir
        name = "shellvars_W%s_%s" % (winid, self.__unique_ident)
        fname = os.path.join(findir, name)
        if shell in ('bash', 'zsh'):
            cmd = \
                """^Uset > %s ^M""" % fname
            self.stuff(cmd, winid)
        return name

    def __save_win(self, winid, ctype, pids_data, ctime, rollback):

        # print (self,winid,ctype,pids_data,ctime,rollback)

        errors = []
        fname = os.path.join(self.basedir, self.savedir, "win_" + winid)
        if rollback[1]:

            #time=linecache.getline(rollback[0],2).strip()
            #copy scrollback

            shutil.move(rollback[1], os.path.join(self.basedir, self.savedir,
                        "hardcopy." + winid))

        basedata_len = 8
        zombie_vector_pos = 8
        zombie_vector = linecache.getline(fname, zombie_vector_pos)

        f = open(fname, "a")
        # import changes from previous savefiles (run with non-restarted windows still running primer)
        if rollback[0]:
            print('Rolling back to primer data in windows running primer')
            rollback_dir = rollback[2]
            target = rollback[0]
            fr = open(target, 'r')
            last_sep = 1
            for (i, line) in enumerate(fr.readlines()[basedata_len:]):
                f.write(line)
                if line == "-\n":
                    last_sep = i
                elif i - last_sep == 6 and line.startswith('vim_'):

                    #import vim files but also update the window number in a filename

                    for filename in glob.glob(os.path.join(rollback_dir,
                            line.strip() + '_*')):
                        try:
                            tvim = "vim_W%s_%s" % (winid, os.path.basename(filename).split("_",
                                    2)[2])
                            tvim = os.path.join(self.basedir, self.savedir,
                                    tvim)
                            shutil.move(filename, tvim)
                        except:
                            errors.append('Unable to rollback vim: %s' %
                                    filename)
                elif i - last_sep == 6 and line.startswith('shellvars_'):
                    print('shellvars')

                    #import shellvars files but also update the window number in the datafile

                    filename = os.path.join(rollback_dir, line.strip())
                    try:
                        tshellvars = "shellvars_W%s_%s" % (winid, os.path.basename(filename).split("_",2)[2])
                        print("%s" % (tshellvars))
                        tshellvars = os.path.join(self.basedir, self.savedir,
                                tshellvars)
                        shutil.move(filename, tshellvars)
                        print(filename,tshellvars)
                    except:
                        errors.append('Unable to rollback shellvars: %s' %
                                filename)
            util.remove(target)
        else:
            pids_data_len = "1"
            if pids_data:
                pids_data_len = str(len(pids_data) + 1)
            f.write(pids_data_len + '\n')
            f.write("-\n")
            f.write("-1\n")
            f.write(zombie_vector)
            f.write("%d\n" % (len(zombie_vector.split('\x00')) - 1))
            f.write(zombie_vector)
            f.write("-1\n")
            f.write("-1\n")
            if pids_data:
                for pid in pids_data:
                    f.write("-\n")
                    for (i, data) in enumerate(pid):
                        if i == 2:
                            if data.endswith('\0\0'):
                                data = data[:len(data) - 1]
                            f.write(str(len(data.split('\x00')) - 1) +
                                    '\n')
                            f.write(str(data) + '\n')
                        else:
                            f.write(str(data) + '\n')
            f.write(ctime)
        f.close()
        return errors

    def __setup_savedir(self, basedir, savedir):
        out("Setting up session directory \"%s\"" % savedir)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
            f = open(os.path.join(basedir, self.blacklistfile), "w")
            f.close()
        return True


