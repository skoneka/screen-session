#!/usr/bin/env python
# file: screen_saver.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: GNU Screen session saving program

'''
issues:
    - program won't recognize telnet and serial window types
'''

import sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,pprint
from ScreenSaver import ScreenSaver
from util import *
from util import tmpdir
import util


logpipeh=None
special_output=None

def doexit(var=0):
    global logpipeh
    if logpipeh:
        logpipeh.close()
    if sys.stdout!=sys.__stdout__:
        sys.stdout.close()
    if special_output:
        special_output.write("R\n")
        special_output.write("%s\n"%(var))
        special_output.close()
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
    global special_output
    
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

    try:
        opts,args = getopt.getopt(sys.argv[argstart:], "e:S:I:mntxXryi:c:fF:i:o:d:hvp:VH:", ["exclude=","idle=","exact","exact-kill","ls","unpack=","full","log=","restore", "mru", "no-vim", "no-scroll=", "no-layout","current-session=","special-output=","force","force-start=","in=", "out=", "dir=","help"])
    except getopt.GetoptError, err:
        out('BAD OPTIONS')
        raise SystemExit
    
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
    mru=False
    force_start=[]
    scroll=[]
    idle=None
    excluded=None
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
            logpipe = a
        elif o == "--unpack":
            unpack = a
        elif o in ("-S","--current-session"):
            current_session = a
        elif o == "--special-output":
            special_output = open(a,'w')
        elif o == "--full":
            bFull = True
        elif o in ("-I","--idle"):
            idle = a
        elif o in ("-V","--no-vim"):
            bVim = False
        elif o in ("-H","--no-scroll"):
            scroll = a
        elif o in ("-x","--exact"):
            bExact = True
        elif o in ("-X","--exact-kill"):
            bExact = True
            bKill=True
        elif o in ("-e","--exclude"):
            excluded = a
        elif o in ("-r","--restore"):
            restore = True
        elif o in ("-f","--force"):
            force = True
        elif o in ("-F","--force-start"):
            force_start = a
        elif o in ("-y","--no-layout"):
            enable_layout = False
        elif o in ("-h","--help"):
            bHelp=True
        elif o in ("-m","mru"):
            mru=True
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
        doexit(1)

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
        doexit(1)
    
    if bHelp:        
        usage()
        doexit(0)
    
    if not projectsdir:
        projectsdir = '.screen-sessions'    
    if bList:
        list_sessions(home,projectsdir,util.archiveend,input)
        doexit(0)
    
    if mode==0:
        if unpack:
            unpackme(home,projectsdir,unpack,util.archiveend,util.tmpdir,bFull)
        else:
            usage()
        doexit(0)
    elif mode==1:
        if not input:
            if current_session:
                input = current_session
            else:
                out("for saving you must specify target Screen session PID as --in")
                doexit("Aborting")
        pid = input
        if not output:
            savedir = pid
        else:
            savedir = output
    elif mode == 2:
        if not input:
            try:
                files=glob.glob(os.path.join(home,projectsdir,'*__win%s'%(util.archiveend)))
                date_file_list=[]
                for file in files:
                    stats = os.stat(file)
                    lastmod_date = time.localtime(stats[8])
                    date_file_tuple = lastmod_date, file
                    date_file_list.append(date_file_tuple)
                date_file_list.sort()
                input=os.path.split(date_file_list[-1][1])[1].rsplit('__',1)[0]
            except:
                out("No recent session to load")
                doexit("Aborting")
        if not output:
            if current_session:
                output = current_session
            else:
                out("for loading you must specify target Screen session PID as --out")
                doexit("Aborting")
        pid = output
        savedir = input
    
    scs=ScreenSaver(pid,projectsdir,savedir)
    scs.command_at(False,"msgminwait 0")

    if idle:
        d_args_d=('-I','-i','--current-session','--idle','--in','--special-output')
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
        command='at 0 exec screen -mdc /dev/null '+scscall 
        scs.idle(idle,command)
        out(':idle %s %s'%(idle,command))
        return 0


    if not scs.exists():
        out('No such session: %s'%pid)
        doexit(1)
        
    if savedir == '__tmp_pack' and mode==1:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1)
    elif savedir == scs.blacklistfile:
        out("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1)
    
    maxwin_real=scs.maxwin()
    if (maxwin==-1):
        maxwin=maxwin_real

    scs.MAXWIN = maxwin
    scs.MAXWIN_REAL = maxwin_real
    scs.force = force
    scs.enable_layout=enable_layout
    scs.restore_previous = restore
    scs.exact=bExact
    scs.bVim=bVim
    scs.mru=mru
    if force_start:
        scs.force_start=force_start.strip().split(',')
    if excluded:
        scs.excluded=excluded.split(',')
    if scroll:
        scs.scroll=scroll.split(',')

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
                scs.Xecho("screen-session saving FAILED. Savefile exists. Use --force")
                out('Savefile exists. Use --force to overwrite.')
                doexit(1)
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
            scs.Xecho("screen-session saving totally FAILED")
            doexit(1)

        if ret:
            out('session saving failed')
            scs.Xecho("screen-session saving FAILED")
        else:
            out('compressing...')
            scs.Xecho("screen-session compressing...")
            removeit(os.path.join(home,projectsdir,savedir_real))
            removeit(os.path.join(util.tmpdir,savedir_real))
            archiveme(util.tmpdir,home,projectsdir,savedir,util.archiveend,savedir_real)
            removeit(os.path.join(home,projectsdir,savedir_tmp))
            removeit(os.path.join(util.tmpdir,savedir_tmp))
            scs.savedir=savedir_real
            savedir=savedir_real
            out('session "%s"'%scs.pid) 
            out('saved as "%s"'%(scs.savedir))
            scs.Xecho("screen-session finished saving as \"%s\""%(savedir))
    elif mode==2: #mode load
        #cleanup old temporary files and directories
        cleantmp(util.tmpdir,home,projectsdir,util.archiveend,scs.blacklistfile,200)
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
                scs.savedir=savedir=input=os.path.basename(matching[0]).split('__win.tar.bz2')[0]
                scs._scrollfile=os.path.join(scs.savedir,"hardcopy.")
                unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir,True)
            else:
                print ('No savefiles match.')
                raise IOError

        try:
            ret = scs.load()
            if special_output and bKill:
                special_output.write("X\n")
                special_output.write("%s\n"%(scs.pid))
                special_output.write("%s\n"%(str(scs.wrap_group_id)))
        except:
            ret=0
            traceback.print_exc(file=sys.stdout)
            out('session loading totally failed')
            scs.Xecho("screen-session loading TOTALLY FAILED")
            doexit(1)

        if ret:
            out('session loading failed')
            scs.Xecho("screen-session loading FAILED")
        else:    
            scs.Xecho("screen-session finished loading")

    else:
        out('No mode specified --load or --save')
    doexit(ret)



if __name__=='__main__':
    try:
        main()
    except IOError:
        print('File access error')
