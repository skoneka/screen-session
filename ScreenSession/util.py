#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    util.py : various utility functions
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

import subprocess
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
import string
import shlex
from six.moves import filter
from six.moves import map
from six.moves import range

archiveend = ""
import tempfile
import pwd
tmpdir = os.path.join(tempfile.gettempdir(), 'screen-session-' + pwd.getpwuid(os.geteuid())[0])
tmpdir_source = os.path.join(tmpdir, '___source')


def _timeout_command_split(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""

    import subprocess
    import datetime
    import os
    import time
    import signal
    cmd = shlex.split(command)
    start = datetime.datetime.now()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               text=True, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.0001)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.readlines()


def timeout_command_list(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""

    import subprocess
    import datetime
    import os
    import time
    import signal
    start = datetime.datetime.now()
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               text=True, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.0001)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.readlines()


def timeout_command(command, timeout):

    #return os.popen(command).readlines()

    global timeout_command
    timeout_command = _timeout_command_split
    return timeout_command(command, timeout)


def out(str, verbosity=0):
    sys.stdout.write(str + '\n')
    sys.stdout.flush()


def touch(fname, times=None):
    try:
        os.utime(fname, times)
    except:
        pass


def linkify(dir, dest, targ):
    try:
        cwd = os.getcwd()
    except:
        cwd = None
    os.chdir(dir)
    try:
        os.remove(targ)
    except:
        pass
    os.symlink(dest, targ)
    if cwd:
        try:
            os.chdir(cwd)
        except:
            pass


def requireme(home, projectsdir, file_in_session, force=False):
    global archiveend
    global tmpdir
    if not force and os.path.isfile(os.path.join(home, projectsdir,
                                    file_in_session)):
        return
    else:
        (fhead, ftail) = os.path.split(file_in_session)
        unpackme(home, projectsdir, fhead, archiveend, tmpdir)


def unpackme(home, projectsdir, savedir, archiveend, tmpdir):
    HOME = os.getenv('HOME')
    if not savedir or not home or not projectsdir or os.path.join(home,
            projectsdir, savedir) == HOME or os.path.join(tmpdir,
            savedir) == HOME:
        return False
    import tarfile
    removeit(os.path.join(home, projectsdir, savedir))
    removeit(os.path.join(tmpdir, savedir))

    if not os.path.exists(os.path.join(home, projectsdir, savedir +
                          archiveend)):
        raise IOError
    os.makedirs(os.path.join(tmpdir, savedir))
    t1 = tarfile.open(os.path.join(home, projectsdir, savedir +
                      archiveend), 'r')
    path = os.path.join(tmpdir, savedir)
    for m in t1.getmembers():
        t1.extract(m, path)
    t1.close()
    try:
        os.symlink(os.path.join(tmpdir, savedir), os.path.join(home,
                   projectsdir, savedir))
    except:
        return False
        pass
    return True


def removeit(path):
    if os.path.islink(path):
        p = os.readlink(path)
        os.remove(path)
    else:
        p = path
    if not os.path.exists(p):
        return 1
    g = glob.glob(os.path.join(p,'*'))
    for f in g:
        if os.path.isdir(f):
            sys.stderr.write('Unable to remove. "%s" has subdirectories!' % p)
            return 2
    try:
        for f in g:
            os.remove(f)
        os.rmdir(p)
    except OSError:
        pass

def remove(path):
    try:
        os.remove(path)
    except:
        sys.stderr.write('Unable to remove "%s"\n' % path)


def cleantmp(tmpdir, home, projectsdir, archiveend, blacklistfile,
             timeout):

    #cleanup old temporary files and directories

    if os.path.join(home, projectsdir) == os.getenv('HOME'):
        return False
    ctime = time.time()
    files_all = glob.glob(os.path.join(home, projectsdir, '*'))
    files_archives = glob.glob(os.path.join(home, projectsdir, '*%s' %
                               archiveend))
    unsorted_remove = list((set(files_all) - set(files_archives)) - set([os.path.join(home,
                        projectsdir, blacklistfile)]))
    sort_remove = []
    for f in unsorted_remove:
        try:
            stats = os.stat(f)
            lastmod_date = time.localtime(stats.st_mtime)
            date_file_tuple = (lastmod_date, f)
            sort_remove.append(date_file_tuple)
        except OSError:
            sort_remove.append((0, f))
    sort_remove.sort(reverse = True)
   
    files_remove = []
    for (d,f) in sort_remove[2:]:
        files_remove.append(f)

    for file in files_remove:
        if os.path.islink(file):
            try:
                delta = ctime - os.path.getmtime(file)
            except:
                delta = timeout + 1
            if delta > timeout:  # if seconds passed since last modification
                removeit(file)
    files_all = glob.glob(os.path.join(tmpdir, '*'))
    files_noremove = glob.glob(os.path.join(tmpdir, '___*'))
    unsorted_remove = list(set(files_all) - set(files_noremove))

    sort_remove = []
    for f in unsorted_remove:
        stats = os.stat(f)
        lastmod_date = time.localtime(stats.st_mtime)
        date_file_tuple = (lastmod_date, f)
        sort_remove.append(date_file_tuple)
    sort_remove.sort(reverse = True)
   
    files_remove = []
    for (d,f) in sort_remove[2:]:
        files_remove.append(f)

    for file in files_remove:
        try:
            delta = ctime - os.path.getmtime(file)
        except:
            delta = timeout + 1
        if delta > timeout:  # if seconds passed since last modification
            removeit(file)


def archiveme(tmpdir, home, projectsdir, savedir, archiveend, target):
    import tarfile
    try:
        t1 = tarfile.open(os.path.join(home, projectsdir, "%s%s" % (savedir,
                          archiveend)), 'w:bz2')
        g = list(glob.glob(os.path.join(home, projectsdir, target)))
        for f in glob.glob(os.path.join(home, projectsdir, target)):
            bInclude = True
            for frm in ['winlist', 'full']:  # do not archive files created by gen_all_windows_full() but not needed by saver
                if f.endswith(frm):
                    bInclude = False
                    break
            if bInclude:
                t1.add(f, os.path.split(f)[1])
        t1.close()
    except Exception:
        print('Failed to archive.')
        raise


def list_sessions(home, projectsdir, archiveend, match, verbose=True):
    if not match:
        match = ""
    files = glob.glob(os.path.join(home, projectsdir, '*%s*%s' % (match,
                      archiveend)))

    date_file_list = []
    for file in files:

        # the tuple element mtime at index 8 is the last-modified-date

        stats = os.stat(file)

        # create tuple (year yyyy, month(1-12), day(1-31), hour(0-23), minute(0-59), second(0-59),
        # weekday(0-6, 0 is monday), Julian day(1-366), daylight flag(-1,0 or 1)) from seconds since epoch
        # note: this tuple can be sorted properly by date and time

        lastmod_date = time.localtime(stats.st_mtime)

        #date_file_tuple = lastmod_date, file, "%d\t"%(stats.st_size)

        date_file_tuple = (lastmod_date, file, "")
        date_file_list.append(date_file_tuple)

    date_file_list.sort()

    if len(date_file_list) > 0:
        out('There are matching saved sessions:')
    else:
        out('There are no matching saved sessions.')

    fileending_l = len(archiveend)
    file_name = None
    for file in date_file_list:

        # extract just the filename

        file_name = os.path.split(file[1])[1]
        file_name = file_name[:len(file_name) - fileending_l]

        # convert date tuple to MM/DD/YYYY HH:MM:SS format

        file_date = time.strftime("%d/%m/%Y\t%H:%M:%S", file[0])
        file_size = file[2]
        if verbose:
            out("%s%s\t%s" % (file_size, file_date, file_name))
    if not verbose:
        out("%s%s\t%s" % (file_size, file_date, file_name))

    if verbose and len(date_file_list) > 0:
        out('%s matching sessions in %s' % (len(date_file_list), os.path.join(home,
            projectsdir)))
    return file_name


def find_in_path(file, path=None):
    """find_in_path(file[, path=os.environ['PATH']]) -> list

  Finds all files with a specified name that exist in the operating system's
  search path (os.environ['PATH']), and returns them as a list in the same
  order as the path.  Instead of using the operating system's search path,
  the path argument can specify an alternative path, either as a list of paths
  of directories, or as a single string seperated by the character os.pathsep.

  If you want to limit the found files to those with particular properties,
  use filter() or which()."""

    if path is None:
        path = os.environ.get('PATH', "")
    if type(path) is type(""):
        path = path.split(os.pathsep)
    return list(filter(os.path.exists, list(map(lambda dir, file=file: os.path.join(dir,
                  file), path))))


def which(file, mode=os.F_OK | os.X_OK, path=None):
    '''which(file[, mode][, path=os.environ[\'PATH\']]) -> list

  Finds all executable files in the operating system\'s search path
  (os.environ[\'PATH\']), and returns them as a list in the same order as the
  path.  Like the UNIX shell command \'which\'.  Instead of using the operating
  system\'s search path, the path argument can specify an alternative path,
  either as a list of paths of directories, or as a single string seperated by
  the character os.pathsep.

  Alternatively, mode can be changed to a different os.access mode to
  check for files or directories other than "executable files".  For example,
  you can additionally enforce that the file be readable by specifying
  mode = os.F_OK | os.X_OK | os.R_OK.'''

    return list(filter(lambda path, mode=mode: os.access(path, mode),
                  find_in_path(file, path)))


def expand_numbers(numstr):
    if not numstr:
        return []
    nums = numstr.split(',')
    n_nums = []
    for n in nums:
        try:
            if '-' in n:
                nmin,nmax = list(map(int, n.split('-')))
                for n_j in range(nmin, nmax + 1):
                    n_nums.append('%s' % n_j)
            else:
                raise
        except:
            n_nums.append('%s' % n)
    return n_nums

def expand_numbers_list(numlist):
    windows = []
    for w in numlist:
        for wn in expand_numbers(w):
            windows.append(wn)
    return windows
