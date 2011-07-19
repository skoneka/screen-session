#!/usr/bin/env python2
#
#    new-window.py : open a new Screen window with the same working directory
#
#    Copyright (C) 2010-2011 Artur Skonecki
#
#    Authors: Artur Skonecki <admin [>at<] adb.cba.pl>
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

import os,sys,platform
import GNUScreen as sc
from GNUScreen import SCREEN

primer=os.path.join(os.path.split(os.path.abspath(__file__))[0],'screen-session-primer -D')
try:
    ppid=int(sys.argv[1])
except:
    ppid=-1
session=sys.argv[2]
tdir = sys.argv[3]
session_arg='-S "%s"'%session
cwin = sc.get_current_window(session)
windows_old = sc.parse_windows(sc.get_windows(session))[0]

if tdir == '':
    f = os.popen(SCREEN+' %s -Q @tty'%session_arg)
    ctty=f.readline()
    f.close()
    if ctty.startswith('/dev'):
        if platform.system() == 'FreeBSD':
            pids=sc.get_tty_pids(ctty)
        else:
            pids=sc._get_tty_pids_pgrep(ctty)

        try:
            p_i=[i for i,x in enumerate(pids) if x==ppid][0]-1
            thepid = pids[p_i]
        except:
            p_i=len(pids)-1
            thepid = pids[p_i]

        info=None
        while not info and p_i>=0:
            try:
                info=sc.get_pid_info(thepid)
            except:
                p_i-=1
                thepid = pids[p_i]
        thedir=info[0]
    else:
        thedir = os.getcwd()
elif tdir == '.':
    thedir = os.getcwd()
elif tdir == '..':
    thedir = os.path.split(os.getcwd())[0]
elif tdir == '~':
    thedir = os.getenv('HOME')
else:
    thedir = tdir

command=SCREEN+' %s -X screen' % (session_arg)

if len(sys.argv)>4:
    command+=' -t "%s"'%(" ".join(["%s"%v for v in sys.argv[4:]]))
else:
    command+=' -t "%s"'%(thedir)

command+=' '+primer+' '+'"%s"'%thedir
try:
    program=sys.argv[4]
    for arg in sys.argv[4:]:
        command+=' "'+arg+'"'
except:
    command+=' "'+os.getenv('SHELL')+'"'
#print (command)
os.system(command)


windows_new=sc.parse_windows(sc.get_windows(session))[0]
windows_diff=sc.find_new_windows(windows_old, windows_new)
target=windows_diff[0]
moveto=int(cwin)+1
sc.move(int(target),moveto,True,session)

