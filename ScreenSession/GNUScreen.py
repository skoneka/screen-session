#!/usr/bin/env python
import os,subprocess,re

def get_pid_info(pid,procdir="/proc"):
    piddir=os.path.join(procdir,pid)
    
    cwd=os.readlink(os.path.join(piddir,"cwd"))
    exe=os.readlink(os.path.join(piddir,"exe"))
    f=open(os.path.join(piddir,"cmdline"),"r")
    cmdline=f.read()
    f.close()
    
    return (cwd,exe,cmdline)

def sort_by_ppid(cpids):
    #print cpids
    cppids={}
    ncpids=[]
    for i,pid in enumerate(cpids):
        try:
            ppid=subprocess.Popen('ps -p %s -o ppid' % (pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split('\n')[1].strip()
            cppids[pid]=ppid
            ncpids.append(pid)
        except:
            pass
    cpids=ncpids

    pid_tail=-1
    pid_tail_c=-1
    cpids_sort=[]
    for i,pid in enumerate(cpids):
        if cppids[pid] not in cppids.keys():
            cpids_sort.append(pid)
            pid_tail=pid
            break;
    
    for j in range(len(cpids)):
        for i,pid in enumerate(cpids):
            if pid_tail==cppids[pid]:
                pid_tail=pid
                cpids_sort.append(pid)
                break;
    cpids=cpids_sort
    return cpids

def get_tty_pids(ctty):
    f = os.popen('lsof -F p %s | cut -c2-' % ctty)
    pids=f.read().strip()
    f.close()
    pids=pids.split('\n')
    pids=sort_by_ppid(pids)
    return pids


def get_session_list():
    screen="screen"
    w=subprocess.Popen('%s -ls' % screen, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if w.startswith('No Sockets'):
        return []
    
    w=w.split('\n')
    w.pop(0)

    wr=[]
    for l in w:
        ent=l.split('\t')
        try:
            if ent[2].startswith('(A'):
                ent[2]=1
            else:
                ent[2]=0
            wr.append((ent[1],ent[2]))
        except:
            break

    return wr

def find_new_session(sessionsp,sessionsn,key=''):
    session=list(set(sessionsn)-set(sessionsp))[0][0]
    return session




def __convert_to_list(s):
    s=s.strip('[').strip(']')
    l=s.split(',')
    ln=[]
    for e in l:
        ln.append(int(e))
    return ln

def parse_windows(windows):
    winendings=re.escape('$*-&@ ')
    winendingsactive=re.escape('*')

    winregex='\s\s\d+[%s]'%(winendings)
    firstwinregex='^\d+[%s]'%(winendings)
    firstwinactiveregex='^\d+[%s][%s]'%(winendingsactive,winendings)
    winactiveregex='\s\s\d+[%s][%s]'%(winendingsactive,winendings)
    
    winids=re.compile(winregex).findall(windows)
    winfirst=re.compile(firstwinregex).findall(windows)
    winactive=re.compile(winactiveregex).findall(windows)
    winactivefirst=re.compile(firstwinactiveregex).findall(windows)
    
    if len(winfirst)>0:
        winnumbers=[int(re.compile('\d+').findall(winfirst[0])[0])]
    else:
        winnumbers=[]
    for id in winids:
        winnumbers.append(int(re.compile('\d+').findall(id)[0]))
    
    winactivenumbers=-1
    if len(winactivefirst)>0:
        winactivenumbers=int(re.compile('\d+').findall(winactivefirst[0])[0])
    elif len(winactive)>0:
        winactivenumbers=int(re.compile('\d+').findall(winactive[0])[0])

    return winnumbers,winactivenumbers


def get_windows(session=None):
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "

    return subprocess.Popen('%s -Q @windows' % screen, shell=True, stdout=subprocess.PIPE).communicate()[0]


def find_new_windows(winids_old,winids_new):
    if winids_old==winids_new:
        return None
    else:
        return list(set(winids_new)-set(winids_old))


def move(windownumber,nextwindownumber,noswitch=False,session=None):
    windownumber=int(windownumber)
    nextwindownumber=int(nextwindownumber)
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "
    
    delta=nextwindownumber-windownumber
    
    if(delta<0):
        sign='-'
    else:
        sign='+'

    delta=abs(delta)

    if noswitch:
        command="%s -X at %d number %s%d"%(screen,windownumber,sign,delta)
        os.system(command)
    else:
        command="%s -X select %d"%(screen,windownumber)
        os.system(command)
        command="%s -X number %s%d"%(screen,sign,delta)
        os.system(command)
    

def get_current_window(session=None):
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "
    return int(subprocess.Popen('%s -Q @number' % screen, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])

def order_windows(win_history):
    #order windows in layout by win_history
    for w in win_history:
        try:
            int(w)
        except:
            break
        #print('window: %s'%w)
        os.system('screen -S %s -X select %s'%(session,w))
        os.system('screen -S %s -X focus' %(session))

def select_window(number,session=None):
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "
    #select region
    if(number!=0 and number<regions_c):
        command='%s %s -X eval'%(screen,session)
        for i in range(0,number):
            command+=' "focus"'
        os.system(command)





def get_regions_count(dumpfile,Session=None):
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "
    try:
        os.remove(dumpfile)
    except:
        pass

    os.system('screen -S %s -X layout dump %s' % (session,dumpfile))
    while not os.path.exists(dumpfile):
        time.sleep(0.01)

    regions_c=int(subprocess.Popen('grep "split" %s |wc -l' % (dumpfile), shell=True, stdout=subprocess.PIPE).communicate()[0])+1

    try:
        os.remove(dumpfile)
    except:
        pass

    return regions_c

def get_regions_count_no_layout(session=None):
    #broken
    if session:
        screen="screen -S %s "%session
    else:
        screen="screen "
    offset_c=0
    os.system('screen -S %s -X screen %s -m %d-%d'%(session,subprogram,os.getpid(),offset_c))
    #fix subprogram
    ident="%s -m %d-%d" %(subprogram,os.getpid(),offset_c)
    offset_c+=1
    region_count=1
    marker = subprocess.Popen('screen -S %s -Q @number' % (session) , shell=True, stdout=subprocess.PIPE).communicate()[0]
    while True:
        os.system('screen -S %s -X focus' % (session) )
        cnum = subprocess.Popen('screen -S %s -Q @number' % (session) , shell=True, stdout=subprocess.PIPE).communicate()[0]
        if cnum==marker:
            break
        else:
            region_count+=1
    finish_them_all(ident)
    return region_count
