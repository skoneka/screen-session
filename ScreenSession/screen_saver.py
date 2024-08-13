#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    screen_saver.py : GNU Screen session saver - processing arguments and
#                      packing / unpacking savefiles
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
from ScreenSaver import ScreenSaver
from util import *
from util import tmpdir
import util
import GNUScreen as sc


def doexit(var=0):
    if sys.stdout != sys.__stdout__:
        sys.stdout.close()
    sys.exit(var)


def usageMode():
    import help
    out(help.help_saver_modes)


def usage():
    import help
    out(help.help_saver)


def main():
    HOME = os.getenv('HOME')
    bad_arg = None

    argstart = 2

    try:
        (opts, args) = getopt.getopt((sys.argv)[argstart:],
                "e:L:s:S:mntxXyc:fF:d:hvp:VWH:l:", [
            "exclude=",
            "exclude-layout=",
            "exact",
            "exact-kill",
            "pack=",
            "unpack=",
            "log=",
            "mru",
            "no-vim",
            "no-shellvars",
            "no-scroll=",
            "no-layout",
            "no-group-wrap",
            "savefile=",
            "session=",
            "force",
            "force-start=",
            "dir=",
            "help",
            ])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err) + '\n')
        doexit(2)

    mode = 0
    util.archiveend = '.tar.bz2'
    pack = None
    unpack = None
    current_session = None
    bNoGroupWrap = False
    bVim = True
    bShellvars = True
    bExact = False
    bKill = False
    bHelp = False
    bList = False
    bFull = False
    mru = False
    force_start = []
    scroll = []
    excluded = []
    excluded_layouts = []
    verbose = False
    log = None
    force = False
    enable_layout = True
    projectsdir = None
    savedir = None
    input = None
    output = None
    try:
        savefile = args[0]
    except:
        savefile = None
    for (o, a) in opts:
        if o == "-v":
            verbose = True
        elif o in ("-n", "--no-group-wrap"):
            bNoGroupWrap = True
        elif o in ("-l", "--log"):
            log = a
        elif o == "--pack":
            pack = a
        elif o == "--unpack":
            unpack = a
        elif o in ("-s", "--savefile"):
            savefile = a
        elif o in "-S":
            if a == '.':
                subprogram = os.path.join(os.path.dirname((sys.argv)[0]),
                        'sessionname.py')
                current_session = util.timeout_command("%s %s \"%s\"" %
                        (os.getenv('PYTHONBIN'), subprogram,
                        current_session), 4)[0].strip()
            else:
                current_session = a
        elif o in "--session":
            current_session = a
        elif o in ("-V", "--no-vim"):
            bVim = False
        elif o in ("-W", "--no-shellvars"):
            bShellvars = False
        elif o in ("-H", "--no-scroll"):
            scroll.append(a)
        elif o in ("-x", "--exact"):
            bExact = True
        elif o in ("-X", "--exact-kill"):
            bExact = True
            bKill = True
        elif o in ("-e", "--exclude"):
            excluded.append(a)
        elif o in ("-L", "--exclude-layout"):
            excluded_layouts.append(a)
        elif o in ("-f", "--force"):
            force = True
        elif o in ("-F", "--force-start"):
            force_start.append(a)
        elif o in ("-y", "--no-layout"):
            enable_layout = False
        elif o in ("-h", "--help"):
            bHelp = True
        elif o in ("-m", "--mru"):
            mru = True
        elif o in ("-d", "--dir"):
            projectsdir = a
        else:
            out('Error parsing: ' + o)
            raise SystemExit
            break
            None

    home = os.path.expanduser('~')

    if log:
        sys.stdout = open(log, 'w')
        sys.stderr = sys.stdout

    if bad_arg:
        out('Unhandled option: %s' % bad_arg)
        doexit(1)

    if (sys.argv)[1] in ('save', 's'):
        mode = 1
        output = savefile
    elif (sys.argv)[1] in ('load', 'l'):
        mode = 2
        input = savefile
    elif (sys.argv)[1] in ('list', 'ls'):
        mode = 0
        bList = True
        input = savefile
    elif (sys.argv)[1] in ("--help", "-h"):
        bHelp = True
    elif (sys.argv)[1] == 'other':
        pass
    else:
        usageMode()
        doexit(1)

    if bHelp:
        usage()
        doexit(0)

    if not projectsdir:
        projectsdir = '.screen-sessions'
    if bList:
        list_sessions(home, projectsdir, util.archiveend, input)
        doexit(0)

    if mode == 0:
        if unpack:
            unpackme(home, projectsdir, unpack, util.archiveend, util.tmpdir)
        elif pack:
            if not output:
                output = pack
            archiveme(util.tmpdir, home, projectsdir, output, util.archiveend,
                      pack + '/*')
        else:
            usage()
        doexit(0)
    elif mode == 1:
        if not input:
            if current_session:
                input = current_session
            else:
                out("for saving you must specify target Screen session -S <sessionname> ")
                doexit(1)
        pid = input
        if not output:
            savedir = pid
        else:
            savedir = output
    elif mode == 2:
        if not input:
            input = list_sessions(home, projectsdir, util.archiveend,
                                  '*', False)
            if not input:
                out("No recent session to load.")
                doexit(1)
        if not output:
            if current_session:
                output = current_session
            else:
                out("for loading you must specify target Screen session -S <sessionname>")
                doexit(1)
        pid = output
        savedir = input

    scs = ScreenSaver(pid, projectsdir, savedir)
    scs.command_at(False, "msgminwait 0")

    if not scs.exists():
        out('No such session: \"%s\"' % pid)
        doexit(1)

    if savedir == '__tmp_pack' and mode == 1:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1)
    elif savedir == scs.blacklistfile:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1)

    scs.force = force
    scs.enable_layout = enable_layout
    scs.exact = bExact
    scs.bVim = bVim
    scs.bShellvars = bShellvars
    scs.mru = mru
    scs.bNoGroupWrap = bNoGroupWrap

    scs.force_start = expand_numbers_list(force_start)
    scs.excluded = expand_numbers_list(excluded)
    scs.excluded_layouts = expand_numbers_list(excluded_layouts)
    scs.scroll = expand_numbers_list(scroll)

    if not os.path.exists(util.tmpdir):
        os.makedirs(util.tmpdir)

    ret = 0
    if mode == 1:  #mode save
        savedir_tmp = savedir + '__tmp'
        savedir_real = savedir
        removeit(os.path.join(home, projectsdir, savedir_tmp))
        removeit(os.path.join(util.tmpdir, savedir_tmp))

        # save and archivize

        if os.path.exists(os.path.join(home, projectsdir, savedir + util.archiveend)):
            if force == False:
                scs.Xecho("screen-session saving FAILED. Savefile exists. Use --force")
                out('Savefile exists. Use --force to overwrite.')
                doexit(1)
            else:
                out('Savefile exists. Forcing...')
        scs.savedir = savedir_tmp
        savedir = savedir_tmp
        try:
            ret = scs.save()
        except:
            ret = 0
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write('session saving totally failed\n')
            scs.Xecho("screen-session saving totally FAILED")
            doexit(1)

        if ret:
            sys.stderr.write('session saving failed\n')
            scs.Xecho("screen-session saving FAILED")
        else:
            out('compressing...')
            scs.Xecho("screen-session compressing...")
            removeit(os.path.join(home, projectsdir, savedir_real))
            removeit(os.path.join(util.tmpdir, savedir_real))
            archiveme(util.tmpdir, home, projectsdir, savedir_real, util.archiveend,
                      savedir_real + '__tmp/*')
            removeit(os.path.join(home, projectsdir, savedir_tmp))
            removeit(os.path.join(util.tmpdir, savedir_tmp))
            scs.savedir = savedir_real
            savedir = savedir_real
            sc.cleanup()
            out('session "%s"' % scs.pid)
            out('saved as "%s"' % scs.savedir)
            scs.Xecho("screen-session finished saving as \"%s\"" %
                      savedir)
    elif mode == 2:  #mode load

        #cleanup old temporary files and directories

        cleantmp(util.tmpdir, home, projectsdir, util.archiveend, scs.blacklistfile,
                 500)

        # unpack and load

        try:
            unpackme(home, projectsdir, savedir, util.archiveend, util.tmpdir)
        except IOError:
            recent = list_sessions(home, projectsdir, util.archiveend,
                                   savedir, True)
            if recent:
                out('Selecting the most recent file: ' + recent)
                scs.savedir = savedir = input = recent
                scs._scrollfile = os.path.join(scs.savedir, "hardcopy.")
                unpackme(home, projectsdir, savedir, util.archiveend,
                         util.tmpdir)
            else:
                raise IOError

        try:
            ret = scs.load()
            if bKill:
                out('Killing wrap group: %s'% scs.wrap_group_id)
                os.system('%s -mdc /dev/null -S SESSION_SAVER_KILL-GROUP %s kill-group -S "%s" %s' %
                (os.getenv('SCREENBIN'),
                os.path.join(os.path.dirname((sys.argv)[0]),"screen-session"),
                scs.pid, str(scs.wrap_group_id)))
        except:
            ret = 0
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write('session loading totally failed\n')
            scs.Xecho("screen-session loading TOTALLY FAILED")
            doexit(1)

        if ret:
            sys.stderr.write('session loading failed\n')
            scs.Xecho("screen-session loading FAILED")
        else:
            scs.Xecho("screen-session finished loading")
    else:

        out('session saver: No such mode')
    doexit(ret)


if __name__ == '__main__':
    try:
        main()
    except IOError:
        sys.stderr.write('File access error\n')
