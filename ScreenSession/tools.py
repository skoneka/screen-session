from ScreenSaver import ScreenSaver
import GNUScreen as sc

def find_pids_in_windows(session,minwin,maxwin,pids):
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
    for win,type,title,tty in sc.gen_all_windows(minwin,maxwin,session):
        try:
            tty = int(os.path.split(tty)[1])
            if tty in ttys:
                wins.append(tuple([win,title]))
        except Exception,x:
            pass
    return wins

def find_files_in_pids(minwin,maxwin,files):
    import os
    cmd='lsof -F p %s | cut -c2-'%(" ".join(["\"%s\""%v for v in files]))
    f = os.popen(cmd)
    pids=f.read().strip().split('\n')
    f.close()
    return pids


def dump(ss,minwin,maxwin):
    for win,type,title,tty in sc.gen_all_windows(minwin,maxwin,ss.pid):
        if type==0:
            type_string="basic"
        elif type==1:
            type_string="group"
        elif type==-1:
            type_string="zombie"
        elif type==2:
            type_string="telnet"
        else:
            type_string="unknown"

        print("%s TYPE\t %s"%(win,type_string))
        print("%s TITL\t %s"%(win,title))
        filter=ss.get_exec(win)
        if filter!=-1:
            print("%s EXEC\t %s"%(win,filter))
        print("%s TTY \t %s"%(win,tty))
        if type==0:
            try:
                pids=sc.get_tty_pids(tty)
            except:
                print ("%s No access"%win)
                pass
            for pid in pids:
                try:
                    cwd,exe,cmd=sc.get_pid_info(pid)
                    print ("%s PID \t %s"%(win,pid))
                    print ("%s P %s CWD \t %s"%(win,pid,cwd))
                    print ("%s P %s EXE \t %s"%(win,pid,exe))
                    print ("%s P %s CMD \t %s"%(win,pid,cmd.split('\0')))
                except:
                    print ("%s PID \t %s\t No permission"%(win,pid))
        print("")

def renumber(session,min,max):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    for win,type,title,tty in sc.gen_all_windows(min,max,session):
        iwin=int(win)
        wins.append((ss.get_group(win)[0],iwin,type))

    win_biggest=wins[len(wins)-1][1]
    for i in range(0,win_biggest+1):
        wins_trans[i]=i

    wins.sort(key=lambda wins:wins[0])

    i=0
    for group,win,type in wins:
        if wins_trans[win]!=i:
            #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
            ss.number(str(i),str(wins_trans[win]))
            tmp=wins_trans[win]
            wins_trans[win]=wins_trans[i]
            wins_trans[i]=tmp
        i+=1

def sort(session,min,max,key=None):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    groups={}
    cgroup=None
    for win,type,title,tty in sc.gen_all_windows(min,max,session):
        iwin=int(win)
        groupid,group=ss.get_group(win)

        lastval=(group,iwin,type,title)
        try:
            groups[group].append(lastval)
        except:
            groups[group]=[lastval]
            
    win_biggest=lastval[1]
    for i in range(0,win_biggest+1):
        wins_trans[i]=i

    i=0
    for group,props in groups.items():
        props.sort(key=lambda wins:wins[3].lower())
        #print( str(len(props))+' : '+group + ' : ' + str(props))
        for group,win,type,title in props:
            if wins_trans[win]!=i:
                #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
                ss.number(str(i),str(wins_trans[win]))
                tmp=wins_trans[win]
                wins_trans[win]=wins_trans[i]
                wins_trans[i]=tmp
            i+=1
    return


def kill_zombie(session,min,max):
    ss=ScreenSaver(session,'/dev/null','/dev/null')

    for win,type,title,tty in sc.gen_all_windows(min,max,session):
        if type==-1:
            ss.kill(win)

def kill_group(session,min,max,groupids):
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
    for win,type,title,tty in sc.gen_all_windows(min,max,session):
        cgroupid,cgroup=ss.get_group(win)
        if(type==1): # group
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
