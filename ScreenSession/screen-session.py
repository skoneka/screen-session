#!/usr/bin/env python
# file: screen-session.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: GNU Screen session saving program

'''
issues:
    - program won't recognize telnet and serial window types
'''

import subprocess,sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re
from ScreenSaver import ScreenSaver
from util import *
import util




def doexit(var=0,waitfor=True):
    if waitfor:
        raw_input('Press any key to exit...')
    if sys.stdout!=sys.__stdout__:
        sys.stdout.close()
    sys.exit(var)

def usageMode():
    out('Usage: screen-session [manage|save|load|list] [options]')

def usage():
    out('Options:\n\
--ls\n\
  \tlist saved sessions\n\
-l --load\n\
  \tloading mode\n\
-s --save\n\
  \tsaving mode\n\
-i --in     <session or directory>\n\
  \tsessionname(saving) or savefile(loading)\n\
-o --out    <session or directory>\n\
  \tsessionname(loading) or savefile(saving)\n\
-m --maxwin <number>\n\
  \tsupply biggest window number in your session\n\
-f --force  <number>\n\
  \tforce saving even if savefile with the same\n\
  \talready exists name exists\n\
-x --exact\n\
  \tload session with the same window numbers, move existing windows\n\
  \tto OTHER_WINDOWS group and delete existing layouts\n\
-X --exact-kill-other\n\
  \tsame as exact, but kills all existing windows\n\
-r --restore\n\
  \treturn to home window and home layout after session loading\n\
-y --no-layout\n\
  \tdisable layout saving/loading\n\
--log       <file>\n\
  \toutput to file instead stdout\n\
-d --dir\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
-w\n\
  \twait for any key when finished\n\
-h --help\n\
  \tshow this message\n\
  \n\
Examples:\n\
$ screen-session --save --maxwin 20 --in SESSIONNAME --out mysavedsession\n\
$ screen-session --load --in mysavedsession --out SESSIONNAME\n\
\n')


VERSION='git'

def main():    

    bad_arg=None
    logpipe=None
    '''
    if "-p" == sys.argv[1]:
        logpipe=sys.argv[2]:
    elif "-p" == sys.argv[2]:
        logpipe=sys.argv[3]:
    elif "-p" == sys.argv[3]:
        logpipe=sys.argv[4]:
    '''


    try :
        opts,args = getopt.getopt(sys.argv[2:], "ntxXryi:c:wfi:o:m:lsd:hvp:", ["exact","exact-kill-other","ls","unpack=","log=","restore","no-layout","current-session=","force","in=", "out=","maxwin=","load","save","dir=","help"])
    except getopt.GetoptError, err:
        bad_arg='BAD OPTIONS'
    
    waitfor=False
    mode = 0
    util.archiveend='.tar.bz2'
    unpack=None
    current_session=None
    bNest=True
    bExact=False
    bKill=False
    bHelp=False
    bList=False
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
        elif o in ("-c","--current-session"):
            current_session = a
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
        elif o in ("-w"):
            # wait for any key press
            # ignore, currently handled in wrapper script
            # waitfor = True
            pass
        elif o in ("-m","--maxwin"):
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
            bad_arg=o
            break;

    home=os.path.expanduser('~')
    
    if log:
        sys.stdout=open(log,'w')
        sys.stderr=sys.stdout
        if logpipe:
            l=open(logpipe,'w')
    elif logpipe:
        sys.stdout=open(logpipe,'w')
        sys.stderr=sys.stdout

        

    out('SCREEN-SESSION ('+VERSION+') - GNU Screen session saver')
    out('written by Artur Skonecki admin<[at]>adb.cba.pl\n')

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
            unpackme(home,projectsdir,unpack,util.archiveend,util.tmpdir,False)
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
        maxwin=scs.get_maxwin()
    elif (maxwin==-1) and (mode==2) and bExact==True:
        out("--exact mode requires --maxwin (biggest window number in current session)")
        maxwin=scs.get_maxwin()


    scs.maxwin = maxwin
    scs.force = force
    scs.enable_layout=enable_layout
    scs.restore_previous = restore
    scs.exact=bExact
    scs.bKill=bKill

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
                out('Savefile exists. Use --force to overwrite')
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
            out('saved as "%s"'%(scs.pid))
            os.system('screen -S %s -X echo "screen-session finished saving"'%scs.pid)
    elif mode==2: #mode load
        #cleanup old temporary files and directories
        cleantmp(util.tmpdir,home,projectsdir,util.archiveend,scs.blacklistfile,scs.lastlink,200)
        # unpack and load
        unpackme(home,projectsdir,savedir,util.archiveend,util.tmpdir,True)
        try:
            ret = scs.load()
            if scs.bKill:
                scs.kill_old_windows()
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
            os.system('screen -S %s -X echo "screen-session finished loading"'%scs.pid)
    else:
        out('No mode specified --load or --save')

    doexit(ret,waitfor)



if __name__=='__main__':
    main()
