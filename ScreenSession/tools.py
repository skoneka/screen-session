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
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session):
        try:
            ctty = int(os.path.split(ctty)[1])
            if ctty in ttys:
                wins.append(tuple([cwin,ctitle]))
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


def dump(ss,showpid=True,reverse=True,sort=False,groupids=[]):
    from sys import stdout
    bShow=True
    windows=[]
    if groupids:
        windows=subwindows(ss.pid,groupids)[1]
    for cwin,cgroupid,cgroup,ctty,ctype,ctypestr,ctitle,cfilter,cscroll,ctime,cmdargs in sc.gen_all_windows_full(ss.pid,reverse,sort):
        if groupids:
            if cwin in windows:
                bShow=True
            else:
                bShow=False
        if bShow:
            print("----------------------------------------")
            lines=[]
            lines.append("%s TYPE  %s\n"%(cwin,ctypestr))
            if cgroupid=='-1':
                groupstr='-1'
            else:
                groupstr=cgroupid+' '+cgroup
            lines.append("%s GRP   %s\n"%(cwin,groupstr))
            lines.append("%s TITL  %s\n"%(cwin,ctitle))
            lines.append("%s CARG  %s\n"%(cwin,cmdargs.split('\0')))
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
                            lines.append ("%s PID   %s CWD %s\n"%(cwin,pid,cwd))
                            lines.append ("%s PID   %s EXE %s\n"%(cwin,pid,exe))
                            cmd=cmd.split('\0')[:-1]
                            lines.append ("%s PID   %s CMD %s\n"%(cwin,pid,cmd))
                            try:
                                if cmd[0].endswith('screen-session-primer') and cmd[1]=='-p':
                                    lines[0]=lines[0][:-1]+" / primer\n"
                                elif cmd[0] in ('vi','vim','viless','vimdiff'): 
                                    lines[0]=lines[0][:-1]+" / VIM\n"
                            except:
                                pass
                        except:
                            lines.append ("%s PID > %s < No permission\n"%(cwin,pid))
            map(stdout.write,lines)

def renumber(session):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session):
        iwin=int(cwin)
        wins.append((iwin,cgroupid,ctype))
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
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session):
        iwin=int(cwin)
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


def kill_zombie(session,groupids=[]):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    if groupids:
        windows=subwindows(session,groupids)[1]
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session):
        if ctype==-1:
            if groupids:
                if cwin in windows:
                    ss.kill(cwin)
            else:
                ss.kill(cwin)

def make_group_tabs(session,groupids,bAll=False):
    group_wins={}
    group_groups={}
    excluded_wins=[]
    excluded_groups=[]
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session):
        if(ctype==1): # group
            if cwin in groupids or bAll:
                excluded_groups.append(cwin)
            try:
                group_groups[cgroupid]+=[cwin]
            except:
                group_groups[cgroupid]=[cwin]
        else: # anything other than group
            if cwin in groupids:
                excluded_wins.append(cwin)
            else:
                try:
                    group_wins[cgroupid]+=[cwin]
                except:
                    group_wins[cgroupid]=[cwin]
    return group_groups,group_wins,excluded_groups,excluded_wins

def subwindows(session,groupids,datafile=None):
    ss=ScreenSaver(session)
    bAll=False
    if groupids[0] in ('cg','current','..'):
        groupids[0]=ss.get_group()[0]
    elif groupids[0] in ('cw','current-window','.'):
        groupids[0]=ss.get_number_and_title()[0]
    elif groupids[0]=='all':
        bAll=True
    group_wins={}
    group_groups={}
    excluded_wins=[]
    excluded_groups=[]
    for cwin,cgroupid,ctype,ctty,ctitle in sc.gen_all_windows_fast(session,datafile):
        if(ctype==1): # group
            if cwin in groupids or bAll or ctitle in groupids:
                excluded_groups.append(cwin)
            try:
                group_groups[cgroupid]+=[cwin]
            except:
                group_groups[cgroupid]=[cwin]
        else: # anything other than group
            if cwin in groupids or ctitle in groupids:
                excluded_wins.append(cwin)
            else:
                try:
                    group_wins[cgroupid]+=[cwin]
                except:
                    group_wins[cgroupid]=[cwin]
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
    for egroup in excluded_groups:
        excluded_wins.append(egroup)
        try:
            for w in group_wins[egroup]:
                excluded_wins.append(w)
        except:
            pass
    return excluded_groups,excluded_wins

def kill_group(session,groupids):
    ss=ScreenSaver(session)
    excluded_groups,excluded_wins=subwindows(session,groupids)
    print('Killing groups: %s'%str(excluded_groups))
    print('All killed windows: %s'%str(excluded_wins))
    for win in excluded_wins:
        ss.kill(win)

    
def kill_win_last_proc(session,win="-1",sig="TERM"):
    from sys import stderr
    import signal,os,platform
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    ctty=ss.tty(win)
    if (ctty is None) or (ctty == -1):
        stderr.write("Window does not exist (%s)\n" % win)
        return False
    if platform.system() == 'FreeBSD':
        pids=sc.get_tty_pids(ctty)
    else:
        pids=sc._get_tty_pids_pgrep(ctty)
    if len(pids) > 0:
        pid = pids[-1]
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
        return True
