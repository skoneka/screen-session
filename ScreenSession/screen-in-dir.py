#!/usr/bin/env python
# file: screen-in-dir.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: start new GNU Screen window in the same working directory

# screen-in-dir sessionname [program] [args..]
import os,sys
import GNUScreen as sc

bPrint=False

try:
    ppid=int(sys.argv[1])
except:
    ppid=-1
print sys.argv
session=sys.argv[2]
session_arg="-S %s"%session

cwin = sc.get_current_window(session)
windows_old = sc.parse_windows(sc.get_windows(session))[0]

f = os.popen('screen %s -Q @tty'%session_arg)
ctty=f.readline()
f.close()
pids=sc.get_tty_pids(ctty)
thepid = pids[len(pids)-1]
if thepid==ppid:
    thepid = pids[len(pids)-2]
info=sc.get_pid_info(thepid)
thedir=info[0]

#os.chdir(thedir)
#command='screen'

command_dir='screen %s -X chdir %s'%(session_arg,thedir)
os.system(command_dir)
command='screen %s -X screen' % (session_arg)

if len(sys.argv)>3:
    command+=' -t "%s"'%(" ".join(["%s"%v for v in sys.argv[3:]]))
else:
    command+=' -t "%s"'%(thedir)


for arg in sys.argv[3:]:
    print arg
    command+=' "'+arg+'"'
print (command)
os.system(command)


windows_new=sc.parse_windows(sc.get_windows(session))[0]
windows_diff=sc.find_new_windows(windows_old, windows_new)
target=windows_diff[0]
moveto=int(cwin)+1
sc.move(int(target),moveto,True,session)
#os.system('screen %s -p %s -X title blah'%(session,endpos))

