from ScreenSaver import ScreenSaver
import GNUScreen as sc

def dump(ss,minwin,maxwin):
    for win,type,title in sc.gen_all_windows(minwin,maxwin,ss.pid):
        if type==0:
            type_string="basic"
        elif type==1:
            type_string="group"
        elif type==-1:
            type_string="zombie"
        else:
            type_string="unknown"

        print("%s TYPE\t %s"%(win,type_string))
        print("%s TITL\t %s"%(win,title))
        filter=ss.get_exec(win)
        if filter!=-1:
            print("%s EXEC\t %s"%(win,filter))
        tty=ss.tty(win)
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
                    print ("%s PID \t %s No permission"%(win,pid))
        print("")

def renumber(session,min,max):
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    wins=[]
    wins_trans={}
    for win,type,title in sc.gen_all_windows(min,max,session):
        iwin=int(win)
        wins.append((ss.get_group(win),iwin,type))

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
    for win,type,title in sc.gen_all_windows(min,max,session):
        iwin=int(win)
        group=ss.get_group(win)

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

    for win,type,title in sc.gen_all_windows(min,max,session):
        if type==-1:
            ss.kill(win)

def kill_group(session,win):
    print ('killing group %s'%win)
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    tty=ss.tty(win)
    if tty!="telnet":
        print('This window is not a group. Aborting.')
        return
    ss.select(win)
    wins=sc.parse_windows(sc.get_windows(session))[0]
    print (wins)
    for w in wins:
       print('killing %s'%w)

def kill_current_group(ss,bKillHomeWindow=False,other_wins=[],homewindow=-1):
    if homewindow<0:
        cwin,ctitle=ss.get_number_and_title()
        homewindow=int(cwin)
    else:
        homewindow=int(homewindow)
    protected=tuple([(homewindow)]+other_wins)
    print (protected)
    cgroup=ss.get_group()
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
    import signal,os
    ss=ScreenSaver(session,'/dev/null','/dev/null')
    ctty=ss.tty(win)
    pids=sc.get_tty_pids(ctty)
    pid = pids[len(pids)-1]

    sig=eval('signal.SIG'+sig)

    os.kill(int(pid),sig)
