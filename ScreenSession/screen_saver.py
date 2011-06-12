#!/usr/bin/env python
# file: screen_saver.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: GNU Screen session saving program


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
    HOME=os.getenv('HOME')
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
        opts,args = getopt.getopt(sys.argv[argstart:], "e:s:S:mntxXryc:fF:d:hvp:VH:l:", ["exclude=","exact","exact-kill","pack=","unpack=","log=","restore", "no-mru", "no-vim", "no-scroll=", "no-layout","no-group-wrap","savefile=","session=","special-output=","force","force-start=","dir=","help"])
    except getopt.GetoptError, err:
        out('BAD OPTIONS')
        raise SystemExit
    
    mode = 0
    util.archiveend='.tar.bz2'
    pack=None
    unpack=None
    current_session=None
    bNoGroupWrap=False
    bVim=True
    bExact=False
    bKill=False
    bHelp=False
    bList=False
    bFull=False
    mru=True
    force_start=[]
    scroll=[]
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
    try:
        savefile=args[0]
    except:
        savefile=None
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-n","--no-group-wrap"):
            bNoGroupWrap=True
        elif o in ("-l","--log"):
            log = a
        elif o == "-p":
            logpipe = a
        elif o == "--pack":
            pack = a
        elif o == "--unpack":
            unpack = a
        elif o in ("-s","--savefile"):
            savefile = a
        elif o in ("-S","--session"):
            current_session = a
        elif o == "--special-output":
            special_output = open(a,'w')
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
        elif o in ("-m","--no-mru"):
            mru=False
        elif o in ("-d","--dir"):
            projectsdir = a
        else:
            out('Error parsing: '+o)
            raise SystemExit
            break;
    
    home=os.path.expanduser('~')
    
    if log:
        sys.stdout=open(log,'w')
        sys.stderr=sys.stdout

    if bad_arg:
        out('Unhandled option: %s'%bad_arg)
        doexit(1)

    if sys.argv[1] in ('save','s'):
        mode=1
        output = savefile
    elif sys.argv[1] in ('load','l'):
        mode=2
        input = savefile
    elif sys.argv[1] in ('list','ls'):
        mode=0
        bList=True
        input = savefile
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
            unpackme(home,projectsdir,unpack,util.archiveend,util.tmpdir)
        elif pack:
            if not output:
                output=pack
            archiveme(util.tmpdir,home,projectsdir,output,util.archiveend,pack+'/*')
        else:
            usage()
        doexit(0)
    elif mode==1:
        if not input:
            if current_session:
                input = current_session
            else:
                out("for saving you must specify target Screen session -S <sessionname> ")
                doexit(1)
        pid = input
        if not output:
            savedir = pid
        else:
            savedir = output
    elif mode == 2:
        if not input:
            input=list_sessions(home,projectsdir,util.archiveend,'*')
            if not input:
                out("No recent session to load.")
                doexit(1)
        if not output:
            if current_session:
                output = current_session
            else:
                out("for loading you must specify target Screen session -S <sessionname>")
                doexit(1)
        pid = output
        savedir = input
    
    scs=ScreenSaver(pid,projectsdir,savedir)
    scs.command_at(False,"msgminwait 0")

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
    scs.bNoGroupWrap=bNoGroupWrap
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
        if os.path.exists(os.path.join(home,projectsdir,savedir+util.archiveend)):
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
            archiveme(util.tmpdir,home,projectsdir,savedir_real,util.archiveend,savedir_real+'__tmp/*')
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
            unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir)
        except IOError:
            recent=list_sessions(home,projectsdir,util.archiveend,savedir)
            if recent:
                print('Selecting the most recent file: '+recent)
                scs.savedir=savedir=input=recent
                scs._scrollfile=os.path.join(scs.savedir,"hardcopy.")
                unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir)
            else:
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
        out('session saver: No such mode')
    doexit(ret)



if __name__=='__main__':
    try:
        main()
    except IOError:
        print('File access error')
