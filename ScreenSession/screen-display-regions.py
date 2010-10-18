#!/usr/bin/env python
# file: screen-display-regions.py
# author: Artur Skonecki
# website http://adb.cba.pl
# description: script for GNU Screen reassembling functionality of tmux display-panes + swap regions + rotate regions

import sys,os,subprocess,time,signal
import GNUScreen as sc

user=os.getenv("USER")
logfile="/tmp/%s-scs-regions-log"%(user)
dumpfile="/tmp/%s-scs-regions"%(user)
inputfile="/tmp/%s-scs-regions-input-%d"%(user,os.getpid())
subprogram='screen-session-primer -nh'
import copy

global win_history

def showhelp():
    print('script reassembling the functionality of tmux display-panes\n\
            Usage: screen-session regions')

def local_copysign(x, y):
    "Return x with the sign of y. Backported from Python 2.6."
    if y >= 0:
        return x * (1 - 2 * int(x < 0))
    else:
        return x * (1 - 2 * int(x >= 0))

def rotate_list(l, offset):
    """
    Rotate a list by (offset) elements. Elements which fall off
    one side are provided again on the other side.
    Returns a rotated copy of the list. If (offset) is 0,
    returns a copy of (l).
    
    Examples:
        >>> rotate_list([1, 2, 3, 4, 5, 6], 2)
        [3, 4, 5, 6, 1, 2]
        >>> rotate_list([1, 2, 3, 4, 5, 6], -2)
        [5, 6, 1, 2, 3, 4]
    """
    if len(l) == 0:
        raise ValueError("Must provide a list with 1 or more elements")
    if offset == 0:
        rv = copy.copy(l)
    else:
        real_offset = offset % int(local_copysign(len(l), offset))
        rv = (l[real_offset:] + l[:real_offset])
    return rv


def handler(signum,frame):
    global win_history
    bSelect=False
    mode=-1
    f=open(inputfile,'r')
    ch=f.readline().strip()
    f.close()
    try:
        number=int(ch[1:])
    except:
        number=0

    os.remove(inputfile)
    if ch[0]=='s':
        mode=1
    elif ch[0]=="'" or ch[0]=='g':
        mode=0
        bSelect=True
    elif ch[0]=="l":
        mode=2
        number=-1*number
    elif ch[0]=="r":
        mode=2
    else:
        mode=0

    
    if number!=-1 and mode==1:
        tmp=win_history[0]
        win_history[0]=win_history[number]
        win_history[number]=tmp
    elif mode==2:
        win_history=rotate_list(win_history,number)

    cleanup()

    if number!=-1 and bSelect:
        select_window(number) 

    sys.exit(0)

def cleanup():
    order_windows()
    kill_screen_windows(session,wins)
    try:
        os.remove(dumpfile)
    except:
        pass
    try:
        os.remove(inputfile)
    except:
        pass

def find_subprograms(ident):
    procs=subprocess.Popen('ps x |grep "%s"' % (ident), shell=True, stdout=subprocess.PIPE).communicate()[0]
    procs=procs.split('\n')
    nprocs=[]
    for p in procs:
        try:
            nprocs.append(int(p.strip().split(' ')[0]))
        except:
            pass
    return nprocs
def kill_screen_windows(session,wins):
    for w in wins:
        os.system('screen -S %s -p %s -X kill'%(session,w))

def order_windows():
    #return to previous windows
    for w in win_history:
        try:
            int(w)
        except:
            break
        print('window: %s'%w)
        os.system('screen -S %s -X select %s'%(session,w))
        os.system('screen -S %s -X focus' %(session))

def select_window(number):
    #select region
    if(number!=0 and number<regions_c):
        command='screen -S %s -X eval'%session
        for i in range(0,number):
            command+=' "focus"'
        os.system(command)


def get_regions_count(session,dumpfile):
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
'''
#broken
def get_regions_count_no_layout(session):
    offset_c=0
    os.system('screen -S %s -X screen %s -m %d-%d'%(session,subprogram,os.getpid(),offset_c))
    #fix helper program
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
'''
def start_subprograms(session,subprogram,inputfile,regions_c,max_commands):
    command1_p='screen -S %s -X screen -t scs-helper %s %s '%(session,subprogram,inputfile)
    command2_p='screen -S %s -X focus'%(session)
    
    command0='screen -S %s -X eval'%(session)
    command1=' "screen -t scs-helper %s %s '%(subprogram,inputfile)
    command2=' "focus"'

    #max_commands=5 # limited length command with screen -X 
    command=command0
    for i in range(0,regions_c):
        command+=command1+str(i)+'"'+command2+" "
        if i%max_commands==0 or i==regions_c-1:
            os.system(command)
            del command
            command=command0

def get_win_history(session,regions_c):
    this_win_history=[]
    for i in range(0,regions_c):
        win=subprocess.Popen('screen -S %s -Q @number'%(session), shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split(' ',1)[0]
        this_win_history.append(win)
        print ('frame %d win %s'%(i,win))
        os.system('screen -S %s -X focus' %(session))
    return this_win_history


if __name__=='__main__':
    sys.stdout=open(logfile,'w')
    sys.stderr=sys.stdout
    session=sys.argv[1]
    win=subprocess.Popen('screen -S %s -Q @number'%(session), shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split(' ',1)[0]
    print ('win before get_regions_count: '+win)
    #regions_c=get_regions_count_no_layout(session,)
    regions_c=get_regions_count(session,dumpfile)

    ident=subprogram+" "+inputfile
    global win_history
    win_history=get_win_history(session,regions_c)
    w1=sc.parse_windows(sc.get_windows(session))[0]
    start_subprograms(session,subprogram,inputfile,regions_c,5)
    w2=sc.parse_windows(sc.get_windows(session))[0]
    print(w1)
    print(w2)
    wins=sc.find_new_windows(w1,w2)
    print(wins)

    signal.signal(signal.SIGUSR1,handler)
    time.sleep(4)

    cleanup()


 
