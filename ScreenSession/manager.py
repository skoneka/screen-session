#!/usr/bin/env python
# file: manager.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: sessions manager with preview in split window

import commands, os, re, sys,time,tempfile,pwd,mmap
import GNUScreen as sc
import util
from ScreenSaver import ScreenSaver

usagestr='\n===HELP===\n\
h[elp]  - show this message\n\
q[uit]  - exit session manager\n\
e[nter] - enter into session\n\
a[ttach] <name> - attach\n\
n[ame] <name>   - rename\n\
s[creen] <args> - create session\n\
w[ipe] - wipe dead sessions\n\
restart - restart session manager\n\
r[efresh] - refresh session list\n\
l[ayout] - toggle layout\n\
kill - kill selected session\n\
save <output> - save session\n\
ALT + T - toggle between regions\n\
'
tui=1
maxtui=3

def menu_tmp(preselect=None):
    # taken from byobu
    PREFIX = "/usr"
    SHELL = os.getenv("SHELL", "/bin/zsh")
    choice = ""
    sessions = []
    text = []
    i = 0
    output = commands.getoutput('screen -ls ')
    if output:
        for s in output.split("\n"):
            s = re.sub(r'\s+', ' ', s)
            if s.find(" ") == 0 and len(s) > 1:
                text.append(s)
                items = s.split(" ")
                sessions.append(items[1])
                i += 1
    command=None
    inputstring=None
    if True:
        sys.stdout.write("\nGNU Screen sessions...\n\n")
        tries = 0
        while tries < 3:
            i = 1
            for s in text:
                sys.stdout.write("  %d. %s\n" % (i, s))
                i += 1
            sys.stdout.write("  %d.  Create a new session\n" % i)
            i += 1
            try:
                command=None
                inputstring=None
                if preselect:
                    inputstring = preselect
                else:
                    inputstring = raw_input("\nChoose 1-%d or command: " % (i-1))
                if inputstring:
                    try:
                        choice=int(inputstring)
                        if choice >= 0 and choice < i:
                            break
                    except:
                        command=inputstring
                        if command.startswith('h'):
                            print(usagestr)
                            raw_input("Press Return to continue" )
                        break
                else:
                    return "enter"
            except KeyboardInterrupt:
                command='quit'
                print ('panic!')
                return command
                break
            except:
                if choice == "":
                    choice = 1
                    break
                tries += 1
                choice = ""
                sys.stderr.write("\nERROR: Invalid input\n");

    if inputstring:
        if command:
            return command
        if choice==0:
            # Create a new session
            return "quit"
        elif choice == i-1:
            return "screen"
        else:
            # Attach to the chosen session; must use the 'screen' binary
            return "attach "+sessions[choice-1]

    # No valid selection, default to the youngest session, create if necessary
    #os.execv(PREFIX+"/bin/byobu", ["", "-AOxRR"])


def prime(fifoname):
    l1=sc.get_session_list()
    cmd='screen -S "MANAGER_NOATTACH" -m -d -c /dev/null python %s %s %s'%(sys.argv[0],'ui',fifoname)
    sys.stderr.write(cmd+'\n')
    os.popen(cmd)
    l2=sc.get_session_list()
    sys.stderr.write('searching for target session..\n')
    session=sc.find_new_session(l1,l2)
    sys.stderr.write('target session = %s\n'%session)

    print ('session: %s'%session)
    return session

def ui2(fifoname):
    sys.stderr.write('starting ui2\n')
    sys.stderr.flush()
    print('ui2 [%s]'%fifoname)
    pipein = open(fifoname, 'r')                 # open fifo as stdio object
    while 1:
        line = pipein.readline( )[:-1]            # blocks until data sent
        print(line)
        #print 'Parent %d got "%s" at %s' % (os.getpid(), line, time.time( ))

ui2pipe=None
def print2pipe(pipeout,line):
    os.write(pipeout,'%s\n'%line)
    pass

def print2ui(line):
    global ui2pipe
    os.write(ui2pipe,'%s\n'%line)
    pass


def usage():
    print2ui(usagestr)

def reset_tui(scs):
    global tui
    print2ui('TUI = %d'%tui)

    if tui==0 or tui==1:
        reset_tui_1(scs)
    elif tui==2:
        reset_tui_2(scs)
    elif tui==3:
        reset_tui_3(scs)
    

def reset_tui_1(scs):
    scs.only()
    scs.split('-v')
    scs.split()
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')
    scs.focus()
    scs.select('1')
    scs.focus('top')

    dinfo=scs.dinfo()
    term_x,term_y=int(dinfo[0]),int(dinfo[1])
    reg_x=None
    reg_y=None
    if(term_x>100):
        reg_x=43
    if(term_y>30):
        reg_y=term_y-15
    if reg_x:
        scs.resize('-h %d'%reg_x)
    if reg_y:
        scs.resize('-v %d'%reg_y)
def reset_tui_3(scs):
    scs.only()
    scs.split()
    scs.split('-v')
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')
    scs.focus()
    scs.select('1')
    scs.focus('top')
def reset_tui_2(scs):
    scs.only()
    scs.split('-v')
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')
    
    dinfo=scs.dinfo()
    term_x,term_y=int(dinfo[0]),int(dinfo[1])
    reg_x=None
    if(term_x>100):
        reg_x=43
    if reg_x:
        scs.resize('-h %d'%reg_x)
def reset_tui_4(scs):
    scs.only()
    scs.split()
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')

def logic(scs,fifoname,fifoname2,session,psession,last_session):
    sys.stderr.write('starting logic\n')
    sys.stderr.flush()
    ret=None
    global ui2pipe
    #os.system('screen -X split -v')
    print 'run opening [%s]'%fifoname
    pipein = open(fifoname, 'r')
    print 'run printing'
    sys.stderr.write("%s %s %s\n"%(sys.argv[0],'ui2',fifoname2))
    sys.stdout.flush()
    scs.screen("python %s %s %s"%(sys.argv[0],'ui2',fifoname2))
    pipeout = os.open(fifoname2, os.O_WRONLY)
    ui2pipe=pipeout
    sys.stdout=os.fdopen(pipeout,'w')
    reset_tui(scs)
    usage()
    if last_session:
        mode,last_session=tui_attach_session(scs,last_session,psession)
        
    #usage()
    mode=None
    try:
        while 1:

            line = pipein.readline()[:-1]            # blocks until data sent
            if not line:
                break;
            else:
                if line:
                    print2ui('UI: %s'%line)
                ret=None                
                e=eval_command(scs,line,last_session,psession)
                if e:
                    try:
                        if e[1]:
                            if e[1]=='\0':
                                last_session=None
                            else:
                                last_session=e[1]
                            print2ui('LOGIC: select %s'%last_session)
                    except:
                        pass
                    try:
                        if e[0]:
                            mode=e[0]
                    except:
                        pass
                    try:
                        if e[2]:
                            psession=e[2]
                    except:
                        pass

                    if (mode and mode!="enter") or (mode=='enter' and last_session):
                        raise SystemExit
                    else:
                        mode=None
    except SystemExit:
        pipein.close()
        scs.quit()
        return str(tui)+';'+str(psession)+';'+str(last_session)+';;;'+str(mode)+';'+str(last_session)+';'

def tui_attach_session(scs,arg,psession):
    #print2ui('LOGIC: attaching \"%s\"'%args[0])
    sys.stderr.write('tui trying to attach %s'%psession)
    scs_target=ScreenSaver(arg)
    if not scs_target.exists():
        print2ui('LOGIC: session does not exists')
        return None,None
    scs.focus('bottom')
    cnum=scs.get_number_and_title()[0]
    if scs.sessionname()==arg:
        print2ui('LOGIC: THIS is session [%s]'%arg)

    elif (psession and psession==arg):
        print2ui('LOGIC: parent session is [%s]'%psession)
        print2ui('LOGIC: Unable to attach loop detected')
    else:
        scs.screen('screen -x \"%s\"'%arg)
        scs.title(arg)
    if int(cnum)>1:
        #print2ui('LOGIC: killing window \"%s\"'%cnum)
        scs.kill(cnum)
    scs.focus('top')
    return None,arg

def eval_command(scs,command,last_session,psession):
    command=command.split(' ',1)
    mode=command[0]
    if len(command)>1:
        args=[]
        for arg in command[1].split(' '):
            args.append(arg)
    else:
        args=['']
    #print2ui('command: %s args: %s'%(command,str(args)))


    if mode.startswith('a'): # attach
        return tui_attach_session(scs,args[0],psession)
    if mode.startswith('d'): # deselect
        print2ui('LOGIC: deselecting' )
        scs.focus('bottom')
        scs.select('-')
        scs.focus('top')
        return None,'\0'
    elif mode=='kill':
        if last_session:
            print2ui('LOGIC: killing session \"%s\"'%last_session)
            scs=ScreenSaver(last_session,'/dev/null','/dev/null')
            scs.quit()
    elif mode.startswith('q'): # quit
        print2ui('LOGIC: quiting...' )
        return 'quit',None
    elif mode.startswith('h'): # help
        usage()
    elif mode.startswith('e'): # enter
        return 'enter',None
    elif mode=='restart': # restart
        print2ui('LOGIC: restarting')
        return 'restart',None
    elif mode.startswith('r'): # refresh 
        print2ui('LOGIC: refreshing')
    elif mode.startswith('l'): # layout
        global tui
        print2ui('LOGIC: toggling layout')
        scs.focus('bottom')
        cnum=scs.get_number_and_title()[0]
        scs.focus('top')
        if tui!=maxtui:
            tui+=1
        else:
            tui=1
        reset_tui(scs)
        if int(cnum)>1:
            scs.focus('bottom')
            scs.select(cnum)
            scs.focus('top')
    elif mode.startswith('w'): # wipe
        print2ui('LOGIC: wiping out dead sessions')
        scs.wipe()
    elif mode.startswith('save'): # save 
        if args[0]:
            arg_out='%s'%args[0]
        else:
            arg_out='%s'%last_session
        print2ui('LOGIC: saving session as %s'%arg_out)
        os.popen('screen-session save --force --log /dev/null --in \"%s\" --out \"%s\"'%(last_session,arg_out))
    elif mode.startswith('s'): # screen
        if args and len(args[0])>0:
            arg=" ".join(["%s"%v for v in args])
        else:
            arg=' '

        cmd='screen -d -m %s'%arg
        print2ui('LOGIC: creating new session: [%s]'%(cmd.strip()))
        l1=sc.get_session_list()
        os.popen(cmd)
        l2=sc.get_session_list()
        newsession=sc.find_new_session(l1,l2)
        return tui_attach_session(scs,newsession,psession)
        
    elif mode.startswith('n'): # name
        if last_session:
            print2ui('LOGIC: renaming session to \"%s\"'%args[0])
            if scs.sessionname() == last_session:
                scs_target=scs
            else:
                scs_target=ScreenSaver(last_session,'/dev/null','/dev/null')

            nsessionname=scs_target.sessionname(args[0])
            print2ui('LOGIC: new sessionname is now [%s]'%nsessionname)
            scs.focus('bottom')
            cnum=scs.get_number_and_title()[0]
            if (psession and psession==last_session):
                psession=nsessionname
                print2ui('LOGIC: parent session is now [%s]'%nsessionname)
            elif nsessionname==scs.sessionname():
                print2ui('LOGIC: THIS is session [%s]'%nsessionname)
            else:
                scs.screen('screen -x \"%s\"'%nsessionname)
                scs.title(nsessionname)
            if int(cnum)>1:
                #print2ui('LOGIC: killing window \"%s\"'%cnum)
                scs.kill(cnum)
            scs.focus('top')
            return None,nsessionname,psession
    else:
        print2ui('LOGIC: no such command')


def ui1(fifoname):
    sys.stderr.write('starting ui1\n')
    sys.stderr.flush()
    print 'ui [%s]'%fifoname
    pipeout = os.open(fifoname, os.O_WRONLY)
    selection=''
    while selection!=None:
        os.system('clear')
        selection=menu_tmp()
        if selection:
            os.write(pipeout,'%s\n'%selection)
    #os.close(pipeout)

       
def attach_session(session):
    sys.stderr.write('attaching %s'%session)
    os.popen('screen -x \"%s\"'%(session))
    
def main():
    global tui
    sys.stderr.write('starting..\n')
    if(sys.argv)==0:
        print('Usage: program [p|ui|ui2] [session or named pipe]')
    if sys.argv[1]=='p':
        try:
            psession=sys.argv[2]
        except:
            psession=None

        tmpdir=os.path.join(tempfile.gettempdir(),'screen-sessions-'+pwd.getpwuid(os.geteuid())[0] )
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
        #files may get deleted by screen-session need to prevent
        fifoname=os.path.join(tmpdir,'__manager_%s_ui'%os.getpid())
        fifoname2=os.path.join(tmpdir,'__manager_%s_ui2'%os.getpid())
        last_session=None
       
        if not os.path.exists(fifoname):
            os.mkfifo(fifoname)
        if not os.path.exists(fifoname2):
            os.mkfifo(fifoname2)
        while True:
            sys.stderr.write('priming..\n')
            session=prime(fifoname)
            scs=ScreenSaver(session,'/dev/null','/dev/null')
            scs.command_at('rendition so ky')
            scs.command_at('bindkey ^[t focus prev')
            scs.command_at('bindkey ^[T focus prev')
            scs.source(os.path.join(os.getenv('HOME'),'.screenrc_MANAGER'))
            data=mmap.mmap(-1,100)
            #pipeout = os.open(fifoname, os.O_WRONLY)
            #os.write(pipeout,'%s\n'%'help')
            
            pid=os.fork()
            if pid==0:
                command=logic(scs,fifoname,fifoname2,session,psession,last_session)
                for i,c in enumerate(command):
                    data[i]=c
                break
            else:
                attach_session(session)
                os.waitpid(pid,0)
                command=data.readline().strip()
                options,command=command.split(';;;',1)
                options=options.split(';')
                command=command.split(';')
                '''
                for m in command:
                    print('[]%d|mode=%s'%(len(m),m
                '''

                tui=int(options[0])
                psession=options[1]
                last_session=options[2]
                if command[0]=='enter':
                    print ("entering \"%s\""%(command[1]))
                    attach_session(command[1])
                elif command[0]=='restart':
                    print('restarting...')
                    pass
                elif command[0]=='new':
                    cmd='screen -m %s'%command[1]
                    print ("creating session: [%s]"%(cmd))
                    os.popen(cmd)
                    
                else:
                    try:
                        os.remove(fifoname)
                    except:
                        pass
                    try:
                        os.remove(fifoname2)
                    except:
                        pass
                    break


    elif sys.argv[1]=='ui':
        fifoname=sys.argv[2]
        ui1(fifoname)
    elif sys.argv[1]=='ui2':
        fifoname=sys.argv[2]
        ui2(fifoname)

if __name__=='__main__':
    if not os.path.exists('/tmp/scs_err'):
        sys.stderr=open('/tmp/scs_err','w')
    else:
        sys.stderr=open('/tmp/scs_err','a')
    main()
