#!/usr/bin/env python
import os,subprocess,re,sys,platform

def get_regions(session):
    from ScreenSaver import ScreenSaver
    from util import tmpdir,remove
    ss=ScreenSaver(session)
    tfile=os.path.join(tmpdir,'___regions-%d'%os.getpid())
    ss.command_at(False,'dumpscreen layout \"%s\"'%tfile)
    while True:
        tfiled=None
        while tfiled==None:
            try:
                tfiled=open(tfile,'r')
            except:
                pass
        ret=[0,tuple(tfiled.readline().strip().split(' ')),tuple(tfiled.readline().strip().split(' '))]
        i=0
        for i,line in enumerate(tfiled):
            if line[0]=='f':
                line=line.split(' ',1)[1].strip().split(' ')
                ret[0]=i
            else:
                line=line.strip().split(' ')
            ret.append(tuple(line))
        tfiled.close()
        if len(ret[-1])==1:
            try:
                region_c=int(ret.pop()[0])
                if region_c==i:
                    ret.insert(0,region_c)
                    break
            except:
                pass
    remove(tfile)
    return ret

def gen_all_windows_fast(session):
    from ScreenSaver import ScreenSaver
    from util import tmpdir,remove
    import linecache
    ss=ScreenSaver(session)
    tfile=os.path.join(tmpdir,'___dump-%d-winlist'%os.getpid())
    ss.query_at("at \# dumpscreen window \"%s\""%(tfile))
    for line in open(tfile,'r'):
        try:
            cwin,cgroupid,ctty,ctitle = line.strip().split(' ',3)
        except:
            cwin,cgroupid,ctty= line.strip().split(' ')
            ctitle=None
        if ctty[0]=='z':
            ctypeid=-1
        elif ctty[0]=='g':
            ctypeid=1
        elif ctty[0]=='t':
            ctypeid=2
        else:
            ctypeid=0
        yield cwin,cgroupid,ctypeid,ctty,ctitle
    remove(tfile)

def gen_all_windows_full(session):
    from ScreenSaver import ScreenSaver
    import string
    from util import tmpdir,removeit,remove
    tdir=os.path.join(tmpdir,'___dump-%d'%os.getpid())
    if not os.path.exists(tdir):
        os.mkdir(tdir)
    ss=ScreenSaver(session)
    tfile=os.path.join(tdir,'winlist')
    ss.command_at(False,"at \# dumpscreen window \"%s\" -F"%(tdir))
    ss.query_at("at \# dumpscreen window \"%s\""%(tfile))
    for line in open(tfile,'r'):
        try:
            cwin,cgroupid,ctty,ctitle = line.strip().split(' ',3)
        except:
            cwin,cgroupid,ctty= line.strip().split(' ')
            ctitle=None
        cwin,ctime,cgroup,ctype,ctitle,cfilter,cscroll=map(string.strip,open(os.path.join(tdir,'win_'+cwin),'r').readlines())
        if ctty[0]=='z':    # zombie
            ctypeid=-1
        elif ctype[0]=='g': # group
            ctypeid=1
        elif ctype[0]=='t': # telnet
            ctypeid=2
        else:               # basic
            ctypeid=0
        try:
            cgroupid,cgroup = cgroup.split(' ')
        except:
            cgroup=ss.none_group
        yield cwin,cgroupid,cgroup,ctty,ctypeid,ctype,ctitle,cfilter,cscroll,ctime
    removeit(tdir)

def _get_pid_info_sun(pid):
    procdir="/proc"
    piddir=os.path.join(procdir,str(pid))
    cwd=os.readlink(os.path.join(piddir,"path","cwd"))
    exe=os.readlink(os.path.join(piddir,"path","a.out"))
    p=os.popen('pargs %s'%pid)
    p.readline()
    args=[]
    for line in p:
        args.append(line.split(': ')[1].rstrip('\n'))
    cmdline="\0".join(["%s"%v for v in args])
    cmdline+="\0"
    return (cwd,exe,cmdline)

def _get_pid_info_bsd(pid):
    procdir="/proc"
    piddir=os.path.join(procdir,str(pid))
    p=os.popen('procstat -f %s'%pid)
    p.readline()
    cwd='/'+p.readline().strip().split('/',1)[1]
    #cwd=os.popen('pwdx '+pid).readline().split(':',1)[1].strip()
    exe=os.readlink(os.path.join(piddir,"file"))
    f=open(os.path.join(piddir,"cmdline"),"r")
    cmdline=f.read()
    if not cmdline.endswith('\0'):
        cmdline+='\0'
    f.close()
    return (cwd,exe,cmdline)

def _get_pid_info_linux(pid):
    procdir="/proc"
    piddir=os.path.join(procdir,str(pid))
    cwd=os.readlink(os.path.join(piddir,"cwd"))
    exe=os.readlink(os.path.join(piddir,"exe"))
    f=open(os.path.join(piddir,"cmdline"),"r")
    cmdline=f.read()
    if not cmdline.endswith('\0'):
        cmdline+='\0'
    f.close()
    
    return (cwd,exe,cmdline)

def get_pid_info(pid):
    global get_pid_info
    p=platform.system()
    if p =='Linux':
        get_pid_info=_get_pid_info_linux
    elif p == 'FreeBSD' :
        get_pid_info=_get_pid_info_bsd
    else:
        get_pid_info=_get_pid_info_sun
    return get_pid_info(pid)


def sort_by_ppid(cpids):
    #print (cpids)
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
    global get_tty_pids
    get_tty_pids=_get_tty_pids_ps_with_cache

    return get_tty_pids(ctty)

def _get_tty_pids_ps_fast(ctty):
    f = os.popen('ps --sort=start_time -o pid -t %s' % ctty)
    pids=f.read().strip()
    f.close()
    npids=[]
    for pid in pids.split('\n')[1:]:
        npids.append(pid.strip())
    return npids

def _get_tty_pids_ps_with_cache(ctty):
    global _get_tty_pids_ps_with_cache
    global get_tty_pids
    global tty_and_pids
    import getpass
    tty_and_pids=_get_tty_pids_ps_with_cache_gen(getpass.getuser())
    get_tty_pids=_get_tty_pids_ps_with_cache_find
    return get_tty_pids(ctty)
def _get_tty_pids_ps_with_cache_gen(user):
    import shlex
    p=os.popen('ps -U %s -o tty,pid,ppid'%user)
    p.readline()
    data={}
    for line in p:
        line=shlex.split(line)
        try:
            line=(int(line[0].strip().split('/')[1]),int(line[1].strip()),int(line[2].strip()))
            try:
                data[line[0]]+=[(line[1],line[2])]
            except:
                data[line[0]]=[(line[1],line[2])]
        except:
            pass
    ndata={}
    for key,val in data.items():
        nval=[]
        parents=[]
        pids=[]
        for pid,parent in val:
            pids.append(pid)
        lastpid=-1
        val_not_set=[]
        for pid,parent in val:
            if parent not in pids:
                nval.append(pid)
                lastpid=pid
            else:
                val_not_set.append((pid,parent))
        lastpid=lastpid
        val_not_set_prev_len=0
        val_not_set_swap=[]
        while len(val_not_set)!=val_not_set_prev_len:
            for pid,parent in val_not_set:
                if parent == lastpid:
                    nval.append(pid)
                    lastpid=pid
                else:
                    val_not_set_swap.append((pid,parent))
            val_not_set_prev_len=len(val_not_set)
            val_not_set = val_not_set_swap
            val_not_set_swap=[]
        ndata[key]=nval
    return ndata
def _get_tty_pids_ps_with_cache_find(ctty):
    global tty_and_pids
    return tty_and_pids[int(ctty.rsplit('/',1)[1])]

def _get_tty_pids_pgrep(ctty):
    ctty=ctty.split('/dev/')[1]
    f = os.popen('pgrep -t %s' % ctty)
    pids=f.read().strip().split('\n')
    f.close()
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
    try:
        session=list(set(sessionsn)-set(sessionsp))[0][0]
        return session
    except:
        return ''




def __convert_to_list(s):
    s=s.strip('[').strip(']')
    l=s.split(',')
    ln=[]
    for e in l:
        ln.append(int(e))
    return ln

def parse_windows(windows):
    winendings=re.escape('$*-&@! ')
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

