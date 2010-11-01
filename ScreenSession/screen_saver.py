#!/usr/bin/env python
# file: screen_saver.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: GNU Screen session saving program

'''
issues:
    - program won't recognize telnet and serial window types
'''

import subprocess,sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,pprint
from ScreenSaver import ScreenSaver
from util import *
import util


logpipeh=None

def doexit(var=0,waitfor=True):
    global logpipeh
    if logpipeh:
        logpipeh.close()
    if waitfor:
        raw_input('Press any key to exit...')
    if sys.stdout!=sys.__stdout__:
        sys.stdout.close()
    sys.exit(var)

def usageMode():
    import help
    out(help.help_saver_modes)
    

def usage():
    import help
    out(help.help_saver)

def main():    

    bad_arg=None
    logpipe=None
    
    try:
        logpipe=sys.argv[2].split('=')[1]
        global logpipeh
        if logpipe:
            logpipeh=open(logpipe,'w')
            sys.stdout=logpipeh
            sys.stderr=logpipeh
        argstart=3
    except:
        argstart=2
        pass

    try :
        opts,args = getopt.getopt(sys.argv[argstart:], "S:I:M:ntxXryi:c:Wfi:o:lsd:hvp:V", ["idle=","exact","exact-kill-other","ls","unpack=","full","log=","restore","no-vim", "no-layout","current-session=","force","in=", "out=","maxwin=","load","save","dir=","help"])
    except getopt.GetoptError, err:
        out('BAD OPTIONS')
        raise SystemExit
    
    waitfor=False
    mode = 0
    util.archiveend='.tar.bz2'
    unpack=None
    current_session=None
    bNest=True
    bVim=True
    bExact=False
    bKill=False
    bHelp=False
    bList=False
    bFull=False
    idle=None
    restore = False
    verbose = False
    log=None
    force = False
    enable_layout = True
    projectsdir =None
    savedir = None
    maxwin = -1
    input=None
    output=None
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o == "-n":
            # no-nest, do not wrap in a screen session
            # ignore, currently handled in wrapper script
            # bNest=False
            pass
        elif o in ("-t","--ls"):
            bList=True
        elif o == "--log":
            log = a
        elif o == "-p":
            #logpipe
            logpipe = a
        elif o == "--unpack":
            unpack = a
        elif o in ("-S","--current-session"):
            current_session = a
        elif o == "--full":
            bFull = True
        elif o in ("-I","--idle"):
            idle = a
        elif o in ("-V","--no-vim"):
            bVim = False
        elif o in ("-x","--exact"):
            bExact = True
        elif o in ("-X","--exact-kill-other"):
            bExact = True
            bKill=True
        elif o in ("-r","--restore"):
            restore = True
        elif o in ("-f","--force"):
            force = True
        elif o in ("-y","--no-layout"):
            enable_layout = False
        elif o in ("-h","--help"):
            bHelp=True
        elif o in ("-W"):
            # wait for any key press
            # ignore, currently handled in wrapper script
            # waitfor = True
            pass
        elif o in ("-M","--maxwin","--daxwin"):
            maxwin = int(a)
        elif o in ("-s","--save"):
            mode = 1
        elif o in ("-l","--load"):
            mode = 2
        elif o in ("-d","--dir"):
            projectsdir = a
        elif o in ("-i","--in"):
            input = a
        elif o in ("-o","--out"):
            output = a
        else:
            out('Error parsing: '+o)
            raise SystemExit
            break;

    home=os.path.expanduser('~')
    
    if log:
        sys.stdout=open(log,'w')
        sys.stderr=sys.stdout


    out('GNU Screen session saver')

    if bad_arg:
        out('Unhandled option: %s'%bad_arg)
        doexit(1,waitfor)

    if sys.argv[1] in ('save','s'):
        mode=1
    elif sys.argv[1] in ('load','l'):
        mode=2
    elif sys.argv[1] in ('list','ls'):
        mode=0
        bList=True
    elif sys.argv[1] in ('--help','-h'):
        bHelp=True
    elif sys.argv[1] == 'other':
        pass
    else:
        usageMode()
        doexit(1,waitfor)
    
    if bHelp:        
        usage()
        doexit(0,waitfor)
    
    if not projectsdir:
        directory = '.screen-sessions'
        projectsdir = directory
    
    if bList:
        list_sessions(home,projectsdir,util.archiveend)
        doexit(0,waitfor)
    
    util.tmpdir=os.path.join(tempfile.gettempdir(),'screen-sessions-'+pwd.getpwuid(os.geteuid())[0] )
    
    if mode==0:
        if unpack:
            unpackme(home,projectsdir,unpack,util.archiveend,util.tmpdir,bFull)
        else:
            usage()
        doexit(0,waitfor)
    elif mode==1:
        if not input:
            if current_session:
                input = current_session
            else:
                out("for saving you must specify target Screen session PID as --in")
                doexit("Aborting",waitfor)
        pid = input
        if not output:
            savedir = pid
        else:
            savedir = output
    elif mode == 2:
        if not input:
            input="last"
            try:
                input=os.readlink(os.path.join(home,projectsdir,input)).rsplit('__',1)[0]
            except:
                out("No recent session to load")
                doexit("Aborting",waitfor)
        if not output:
            if current_session:
                output = current_session
            else:
                out("for loading you must specify target Screen session PID as --out")
                doexit("Aborting",waitfor)
        pid = output
        savedir = input
    

    
    scs=ScreenSaver(pid,projectsdir,savedir)

    if idle:
        d_args_d=('-I','-i','--current-session','--idle','--in')
        nargv=[]
        bSkipNext=False
        for arg in sys.argv:
            if arg in d_args_d:
                bSkipNext=True
            elif bSkipNext:
                bSkipNext=False
            else:
                if not arg.startswith('logpipe'):
                    nargv.append(arg)
        nargv[0]=util.which('screen-session')[0]
        scscall=nargv.pop(0)
        scscall+=' '+nargv.pop(0)
        for arg in nargv:
            scscall+=" "+arg
        scscall+=" --in "+input
        command='exec sh -c \"screen '+scscall+' > /dev/null\"' 
        scs.idle(idle,command)
        out(':idle %s %s'%(idle,command))
        return 0


    if not scs.exists():
        out('No such session: %s'%pid)
        doexit(1,waitfor)
        
    if savedir in (scs.lastlink,'__tmp_pack') and mode==1:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1,waitfor)
    elif savedir == scs.blacklistfile:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1,waitfor)
    
    if (maxwin==-1) and (mode==1):
        out("for saving specify --maxwin (biggest window number in session)")
        maxwin=scs.maxwin()
    elif (maxwin==-1) and (mode==2) and bExact==True:
        out("--exact option requires --maxwin (biggest window number in current session)")
        maxwin=scs.maxwin()


    scs.MAXWIN = maxwin
    scs.force = force
    scs.enable_layout=enable_layout
    scs.restore_previous = restore
    scs.exact=bExact
    scs.bKill=bKill
    scs.bVim=bVim

    if not os.path.exists(util.tmpdir):
        os.makedirs(util.tmpdir)
    
    ret=0
    if mode==1: #mode save
        savedir_tmp=savedir+'__tmp'
        savedir_real=savedir
        removeit(os.path.join(home,projectsdir,savedir_tmp))
        removeit(os.path.join(util.tmpdir,savedir_tmp))
        # save and archivize
        if os.path.exists(os.path.join(home,projectsdir,savedir+'__win'+util.archiveend)):
            if force==False:
                os.system('screen -S %s -X echo "screen-session saving FAILED. Savefile exists."'%scs.pid)
                out('Savefile exists. Use --force to overwrite.')
                doexit(1,waitfor)
            else:
                out('Savefile exists. Forcing...')
        scs.savedir=savedir_tmp
        savedir=savedir_tmp
        try:
            ret = scs.save()
        except:
            ret=0
            traceback.print_exc(file=sys.stdout)
            out('session saving totally failed')
            os.system('screen -S %s -X echo "screen-session TOTALLY FAILED"'%scs.pid)
            doexit(1,waitfor)

        if not ret:
            out('session saving failed')
            os.system('screen -S %s -X echo "screen-session FAILED"'%scs.pid)
        else:
            removeit(os.path.join(home,projectsdir,savedir_real))
            removeit(os.path.join(util.tmpdir,savedir_real))
            archiveme(util.tmpdir,home,projectsdir,savedir,util.archiveend,scs.lastlink,savedir_real)
            removeit(os.path.join(home,projectsdir,savedir_tmp))
            removeit(os.path.join(util.tmpdir,savedir_tmp))
            scs.savedir=savedir_real
            savedir=savedir_real
            out('session "%s"'%scs.pid) 
            out('saved as "%s"'%(scs.savedir))
            os.system('screen -S %s -X echo "screen-session finished saving as \"%s\""'%(scs.pid,savedir))
    elif mode==2: #mode load
        #cleanup old temporary files and directories
        cleantmp(util.tmpdir,home,projectsdir,util.archiveend,scs.blacklistfile,scs.lastlink,200)
        # unpack and load
        try:
            unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir,True)
        except IOError:
            g = glob.glob(os.path.join(home, projectsdir, '*%s*__win.tar.bz2'%savedir))
            matching = list(g)
            matching_len=len(matching)
            if matching_len>1:
                print ('%d savefiles match:'%matching_len)
                for f in matching:
                    print('\t'+os.path.basename(f).split('__win.tar.bz2')[0])
                raise IOError
            elif matching_len==1:
                scs.savedir=savedir=os.path.basename(matching[0]).split('__win.tar.bz2')[0]
                unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir,True)
            else:
                print ('No savefiles match.')
                raise IOError

        try:
            ret = scs.load()
        except:
            ret=0
            traceback.print_exc(file=sys.stdout)
            out('session loading totally failed')
            os.system('screen -S %s -X echo "screen-session TOTALLY FAILED"'%scs.pid)
            doexit(1,waitfor)

        if not ret:
            out('session loading failed')
            os.system('screen -S %s -X echo "screen-session FAILED"'%scs.pid)
        else:    
            if scs.bKill:
                #scs.kill_old_windows()
                pass
                import tools
                print ('homewindow:'+scs.homewindow)
                print ('select:'+str(scs.win_none_g))
                scs.select(scs.win_none_g)
                print ('group:'+scs.get_group())
                tools.kill_current_group(scs,False,[scs.wrap_group_id],scs.homewindow)
            os.system('screen -S %s -X echo "screen-session finished loading"'%scs.pid)

    else:
        out('No mode specified --load or --save')
    doexit(ret,waitfor)



if __name__=='__main__':
    try:
        main()
    except IOError:
        print('File access error')
