#!/usr/bin/env python

# screen-in-dir sessionname [program] [args..]
import os,sys
import GNUScreen as sc

session="%s"%sys.argv[1]
session_arg="-S %s"%session

cwin = sc.get_current_window(session)
windows_old = sc.parse_windows(sc.get_windows(session))[0]
print windows_old

f = os.popen('screen %s -Q @tty'%session_arg)
ctty=f.readline()
f.close()
print ctty
f = os.popen('lsof -F p %s | cut -c2-' % ctty)
pids=f.read().strip()
f.close()
pids=pids.split('\n')
pids=sc.sort_by_ppid(pids)
thepid = pids[len(pids)-1]

thedir = '/proc/%s/cwd' % thepid
print thedir

os.chdir(thedir)

#command='screen %s -X screen' % (session_arg)
command='screen'

for arg in sys.argv[2:]:
    command+=' '+arg
print command
#os.system(command)

windows_new=sc.parse_windows(sc.get_windows(session))[0]
print windows_new
windows_diff=sc.find_new_windows(windows_old, windows_new)
target=windows_diff[0]
print '%s to %s'%(target,cwin)
sc.move(int(target),int(cwin)+1,True,session)

