#!/usr/bin/env python
# file: screen-in-dir.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: start new GNU Screen window in the same working directory

# screen-in-dir sessionname [program] [args..]
import os,sys
import GNUScreen as sc

primer='screen-session-primer -D'
try:
    ppid=int(sys.argv[1])
except:
    ppid=-1
session=sys.argv[2]
session_arg="-S %s"%session
cwin = sc.get_current_window(session)
windows_old = sc.parse_windows(sc.get_windows(session))[0]

f = os.popen('screen %s -Q @tty'%session_arg)
ctty=f.readline()
f.close()
pids=sc.get_tty_pids(ctty)
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

command='screen %s -X screen' % (session_arg)

if len(sys.argv)>3:
    command+=' -t "%s"'%(" ".join(["%s"%v for v in sys.argv[3:]]))
else:
    command+=' -t "%s"'%(thedir)

command+=' '+primer+' '+'"%s"'%thedir
try:
    program=sys.argv[3]
    for arg in sys.argv[3:]:
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

