from ScreenSaver import ScreenSaver
import GNUScreen as sc

def find_pids_in_windows(session,pids):
    import getpass,os
    tty_and_pids=sc._get_tty_pids_ps_with_cache_gen(getpass.getuser())
    #print(tty_and_pids)
    ttys=[]
    for tty,tpids in tty_and_pids.items():
        #print('%s %s %s'%(pids,tty,tpids))
        for pid in pids:
            if pid in tpids:
                ttys.append(tty)
    wins=[]
    for win,groupid,ctype,tty in sc.gen_all_windows_fast(session):
        try:
            tty = int(os.path.split(tty)[1])
            if tty in ttys:
                wins.append(tuple([win,""]))
        except Exception,x:
            pass
    return wins

def find_files_in_pids(files):
    import os
    cmd='lsof -F p %s | cut -c2-'%(" ".join(["\"%s\""%v for v in files]))
    f = os.popen(cmd)
    pids=f.read().strip().split('\n')
    f.close()
    return pids


def dump(ss,showpid=True):
    from sys import stdout
    for cwin,cgroupid,cgroup,ctty,ctype,ctypestr,ctitle,cfilter,cscroll,ctime in sc.gen_all_windows_full(ss.pid):
        print("----------------------------------------")
        lines=[]
        lines.append("%s TYPE  %s\n"%(cwin,ctypestr))
        lines.append("%s GRP   %s\n"%(cwin,cgroupid+' '+cgroup))
        lines.append("%s TITL  %s\n"%(cwin,ctitle))
        if cfilter!='-1':
            lines.append("%s EXEC  %s\n"%(cwin,cfilter))
        if ctype==0:
            lines.append("%s TTY   %s\n"%(cwin,ctty))
            if showpid:
                try:
                    pids=sc.get_tty_pids(ctty)
                except:
                    lines.append ("%s No access\n"%cwin)
                    pass
                for pid in pids:
                    try:
                        cwd,exe,cmd=sc.get_pid_info(pid)
                        lines.append ("%s PID > %s <\n"%(cwin,pid))
                        lines.append ("%s PID   %s CWD %s\n"%(cwin,pid,cwd))
                        lines.append ("%s PID   %s EXE %s\n"%(cwin,pid,exe))
                        cmd=cmd.split('\0')[:-1]
                        lines.append ("%s PID   %s CMD %s\n"%(cwin,pid,cmd))
                        try:
                            if cmd[0].endswith('screen-session-primer') and cmd[1]=='-p':
                                lines[0]="%s TYPE   primer\n"%(cwin)
                        except:
                            pass
                    except:
                        lines.append ("%s PID   %s No permission\n"%(cwin,pid))
        map(stdout.write,lines)

def renumber(session):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    for win,groupid,ctype,tty in sc.gen_all_windows_fast(session):
        iwin=int(win)
        wins.append((iwin,groupid,ctype))
        wins_trans[iwin]=iwin

    wins.sort(key=lambda wins:wins[0])
    print wins_trans
    i=0
    for win,groupid,ctype in wins:
        if wins_trans[win]!=i:
            #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
            ss.number(str(i),str(wins_trans[win]))
            tmp=wins_trans[win]
            try:
                wins_trans[win]=wins_trans[i]
            except:
                wins_trans[win]=-1
            wins_trans[i]=tmp
        i+=1
    print wins_trans

def sort(session,key=None):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    groups={}
    cgroup=None
    for win,groupid,ctype,tty in sc.gen_all_windows_fast(session):
        iwin=int(win)
        lastval=(groupid,iwin,ctype,ss.title('',iwin))
        try:
            groups[groupid].append(lastval)
        except:
            groups[groupid]=[lastval]
        wins_trans[iwin]=iwin

    i=0
    for group,props in groups.items():
        try:
            props.sort(key=lambda wins:wins[3].lower())
        except:
            print('FAIL')
            print( str(len(props))+' : '+group + ' : ' + str(props))
            pass
        #print( str(len(props))+' : '+group + ' : ' + str(props))
        for groupid,win,ctype,title in props:
            if wins_trans[win]!=i:
                #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
                ss.number(str(i),str(wins_trans[win]))
                tmp=wins_trans[win]
                try:
                    wins_trans[win]=wins_trans[i]
                except:
                    wins_trans[win]=-1
                wins_trans[i]=tmp
            i+=1
    return


def kill_zombie(session):
    ss=ScreenSaver(session,'/dev/null','/dev/null')

    for win,groupid,ctype,tty in sc.gen_all_windows_fast(session):
        if ctype==-1:
            ss.kill(win)

def kill_group(session,groupids):
    #sys.stdout=open('/tmp/___log_kill_group','w')
    #sys.stderr=sys.stdout
    ss=ScreenSaver(session)
    bAll=False
    if groupids[0]=='current':
        groupids[0]=ss.get_group()[0]
    elif groupids[0]=='all':
        bAll=True
    group_wins={}
    group_groups={}
    excluded_wins=[]
    excluded_groups=[]
    for win,cgroupid,ctype,tty in sc.gen_all_windows_fast(session):
        if(ctype==1): # group
            if win in groupids or bAll:
                excluded_groups.append(win)
            try:
                group_groups[cgroupid]+=[win]
            except:
                group_groups[cgroupid]=[win]
        else: # anything other than group
            if win in groupids:
                excluded_wins.append(win)
            else:
                try:
                    group_wins[cgroupid]+=[win]
                except:
                    group_wins[cgroupid]=[win]
    excluded_groups_tmp=[]
    while excluded_groups:
        egroup=excluded_groups.pop()
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
    print('Killing groups: %s'%str(excluded_groups))
    for egroup in excluded_groups:
        excluded_wins.append(egroup)
        try:
            for w in group_wins[egroup]:
                excluded_wins.append(w)
        except:
            pass
    print('All killed windows: %s'%str(excluded_wins))
    for win in excluded_wins:
        ss.kill(win)

def kill_current_group(ss,bKillHomeWindow=False,other_wins=[],homewindow=-1):
    if homewindow<0:
        cwin,ctitle=ss.get_number_and_title()
        homewindow=int(cwin)
    else:
        homewindow=int(homewindow)
    protected=tuple([(homewindow)]+other_wins)
    print (protected)
    cgroup=ss.get_group()[1]
    print ('removing windows from group %s'%cgroup)
    while True:
        wins=sc.parse_windows(sc.get_windows(ss.pid))[0]
        print( wins)
        if len(wins)<=len(protected):
            break
        for w in wins:
            if w not in protected:
                print('removing %s'%w)
                ss.kill(w)
    for w in other_wins:
        ss.kill(w)
    for w in protected:
        if w != homewindow:
            print('removing protected %s'%w)
            ss.kill(w)
    if bKillHomeWindow:
        print('removing homewindow %s'%homewindow)
        ss.kill(homewindow)



    
def kill_win_last_proc(session,win="-1",sig="TERM"):
    import signal,os,platform
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    ctty=ss.tty(win)
    if platform.system() == 'FreeBSD':
        pids=sc.get_tty_pids(ctty)
    else:
        pids=sc._get_tty_pids_pgrep(ctty)
    pid = pids[-1]

    sig=eval('signal.SIG'+sig)
    os.kill(int(pid),sig)
