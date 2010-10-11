from ScreenSaver import ScreenSaver
import GNUScreen as sc

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
        group=ss.getgroup(win)
        if cgroup!=group:
            cgroup=group
            wins=groups[cgroup]=[]
        groups[cgroup].append((group,iwin,type,title))

    win_biggest=wins[len(wins)-1][1]
    for i in range(0,win_biggest+1):
        wins_trans[i]=i

    wins.sort(key=lambda wins:wins[3].lower())

    wins.sort(key=lambda wins:wins[0])
    nwins=[]



    i=0
    for group,win,type,title in wins:
        if wins_trans[win]!=i:
            #print("win %d(%d)(%s) as %d"%(wins_trans[win],win,group,i))
            ss.number(str(i),str(wins_trans[win]))
            tmp=wins_trans[win]
            wins_trans[win]=wins_trans[i]
            wins_trans[i]=tmp
        i+=1

def kill_zombie(session,min,max):
    ss=ScreenSaver(session,'/dev/null','/dev/null')

    for win,type,title in sc.gen_all_windows(min,max,session):
        if type==-1:
            ss.kill('',win)
