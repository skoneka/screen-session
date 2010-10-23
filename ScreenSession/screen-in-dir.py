#!/usr/bin/env python
# file: screen-in-dir.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: start new window in the same working directory

# screen-in-dir sessionname [program] [args..]
import os,sys
import GNUScreen as sc

def out(str,active=False):
    if active:
        sys.stdout.write(str+'\n')

bPrint=False

try:
    ppid=int(sys.argv[1])
except:
    ppid=-1

session=sys.argv[2]
out('session = '+session,bPrint)
session_arg="-S %s"%session

cwin = sc.get_current_window(session)
windows_old = sc.parse_windows(sc.get_windows(session))[0]
out(str(windows_old),bPrint)

f = os.popen('screen %s -Q @tty'%session_arg)
ctty=f.readline()
f.close()
out(ctty,bPrint)
pids=sc.get_tty_pids(ctty)
thepid = pids[len(pids)-1]
if thepid==ppid:
    thepid = pids[len(pids)-2]
info=sc.get_pid_info(thepid)
thedir=info[0]

out(thedir,bPrint)

os.chdir(thedir)

#command='screen %s -X screen' % (session_arg)
command='screen'
if len(sys.argv)>3:
    command+=' -t "%s"'%(" ".join(["%s"%v for v in sys.argv[3:]]))
else:
    command+=' -t "%s"'%(thedir)


for arg in sys.argv[3:]:
    command+=' '+arg
out(command,bPrint)
os.system(command)


windows_new=sc.parse_windows(sc.get_windows(session))[0]
out(str(windows_new),bPrint)
windows_diff=sc.find_new_windows(windows_old, windows_new)
target=windows_diff[0]
out('%s to %s'%(target,cwin),bPrint)
moveto=int(cwin)+1
sc.move(int(target),moveto,True,session)
#os.system('screen %s -p %s -X title blah'%(session,endpos))

