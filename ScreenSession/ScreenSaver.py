
import sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,linecache

from util import out,requireme,linkify,which,timeout_command
import util
import GNUScreen as sc

class ScreenSaver(object):
    """class storing GNU screen sessions"""
    timeout=3
    pid="" # actually it is sessionname
    basedir=""
    projectsdir=".screen-sessions"
    savedir=""
    MAXWIN=-1
    MAXWIN_REAL=-1
    MINWIN_REAL=0
    force=False
    enable_layout = False
    restore_previous = False
    exact=False
    bVim=True
    mru=True
    force_start=[]
    scroll=[]
    group_other='OTHER_WINDOWS'
    homewindow=""
    sc=None
    wrap_group_id=None
    
    primer_base="screen-session-primer"
    primer=primer_base
    primer_arg="-p"
    
    # blacklist file in projects directory
    blacklistfile="BLACKLIST"
    
    # old static blacklist
    blacklist = ("rm","shutdown")
    # user submitted list of excluded windows
    excluded = None
   
    vim_names = ('vi','vim','viless','vimdiff')
    __unique_ident=None
    __wins_trans = {}
    __scrollbacks=[]
    __layouts_loaded=False

    def __init__(self,pid,projectsdir='/dev/null',savedir='/dev/null'):
        self.homedir=os.path.expanduser('~')
        self.projectsdir=str(projectsdir)
        self.basedir=os.path.join(self.homedir,self.projectsdir)
        self.savedir=str(savedir)
        self.pid=str(pid)
        self.set_session(self.pid)
        self.primer=os.path.join(os.path.dirname(sys.argv[0]),self.primer)
        self._scrollfile=os.path.join(self.savedir,"hardcopy.")

    def set_session(self,sessionname):
        self.sc='%s -S %s'%(which('screen')[0],sessionname)
        self.__unique_ident="S%s_%s"%(sessionname.split('.',1)[0],time.strftime("%d%b%y_%H-%M-%S"))

    def save(self):
        self.homewindow,title=self.get_number_and_title()
        out("\nCreating directories:")
        if not self.__setup_savedir(self.basedir,self.savedir):
            return 1

        if self.enable_layout:
            out("\nSaving layouts:")
            self.homewindow_last,title=self.get_number_and_title()
            self.__save_layouts()
            out("")

        out("\nSaving windows:")
        self.__save_screen()
        
        out("\nCleaning up:")
        self.__scrollback_clean()
        return 0

    def load(self):
        if 'all' in self.force_start:
                self.primer_arg+='S'
                self.force_start=[]
        if 'all' in self.scroll:
            self._scrollfile=None
        out('session "%s" loading "%s"' % (self.pid,os.path.join(self.basedir,self.savedir)))
        #check if the saved session exists and get the biggest saved window number and a number of saved windows
        maxnewwindow=0
        newwindows=0
        try:
            winlist=list(glob.glob(os.path.join(self.basedir,self.savedir,'win_*')))
            newwindows=len(winlist)
            out('%d new windows'%newwindows)
        except Exception,e:
            out('Unable to open.')
            out(str(e))
            return 1

        # keep original numbering, move existing windows
        self.homewindow=self.number()
        if self.exact:
            maxnewwindow=-1
            for w in winlist:
                try:
                    w = int(w.split('_',1)[1])
                    if w > maxnewwindow:
                        maxnewwindow = w
                except:
                    pass
                
            out('Biggest new window number: %d'%maxnewwindow)
            if self.enable_layout:
                self.__remove_all_layouts()
            self.__move_all_windows(maxnewwindow+1,self.group_other,False)
        
        self.homewindow=self.number()
        out("\nLoading windows:")
        self.__load_screen()
        if self.enable_layout:
            out("\nLoading layouts:")
            self.__load_layouts()
        if self.mru:
            out("\nRestoring Most Recently Used windows order.")
            self.__restore_mru()
        return 0

    def exists(self):
        msg=self.echo('test')
        try:
            if msg.startswith('No'): # 'No screen session found'
                return False
            else:
                return True
        except:
            return False

    def __escape_bad_chars(self,str):
        # some characters are causing problems when setting window titles
        return str.replace('|','I').replace('\\','\\\\\\\\')# how to properly escape "|"?

    def __load_screen(self):
        homewindow=self.homewindow
        # out ("Homewindow is " +homewindow)
        
        #check if target Screen is currently in some group and set hostgroup to it
        hostgroupid,hostgroup = self.get_group(homewindow)

        if self.exact:
            rootgroup='none'
            hostgroup='none'
        else:
            #create a root group and put it into host group
            rootgroup="restore_"+self.savedir
            self.screen('-t \"%s\" %s //group' % (rootgroup,0 ) )
            self.group(False,'%s' % (hostgroup) )
        
        rootwindow=self.number()
        out("restoring Screen session inside window %s (%s)" %(rootwindow,rootgroup))

        out('NUMBER; TIME; GROUP; TYPE; TITLE; FILTER; SCROLLBACK; PROCESSES;')
        wins=[]
        for id in range(0,int(self.MAXWIN_REAL)):
            try:
                filename=os.path.join(self.basedir,self.savedir,"win_"+str(id))
                if os.path.exists(filename):
                    f=open(filename)
                    win=list(f)[0:8]
                    f.close()
                    win=self.__striplist(win)
                    out (str(win))
                    wins.append((win[0], win[1], win[2], win[3], self.__escape_bad_chars(win[4]), win[5], win[6],win[7]))
            except:
                out('%s Unable to load window'%id)

        for win,time,group,type,title,filter,scrollback_len,processes in wins:
            self.__wins_trans[win]=self.__create_win(self.exact,self.__wins_trans,self.pid,hostgroup,rootgroup,win,time,group,type,title,filter,scrollback_len,processes)
        
        for win,time,group,type,title,filter,scrollback_len,processes in wins:
            try:
                groupid,group=group.split(' ',1)
            except:
                groupid="-1"
                group=""
            self.__order_group(self.__wins_trans[win],self.pid,hostgroup,rootwindow,rootgroup,win,time,groupid,group,type,title,filter,scrollback_len,processes)
        
        out ("Rootwindow is "+rootwindow)
        if self.wrap_group_id:
            out ("Wrap group is "+self.wrap_group_id)
        self.select(rootwindow)
        
    # Take a list of string objects and return the same list
    # stripped of extra whitespace.
    def __striplist(self,l):
        return([x.strip() for x in l])


    def __create_win(self,keep_numbering,wins_trans,pid,hostgroup,rootgroup,win,time,group,type,title,filter,scrollback_len,processes):
        if keep_numbering:
            winarg=win
        else:
            winarg=""
        
        if type[0]=='b':
            if win in self.force_start:
                primer_arg=self.primer_arg+'S'
            else:
                primer_arg=self.primer_arg
            if win in self.scroll or not self._scrollfile or not os.path.exists(os.path.join(self.homedir,self.projectsdir,self._scrollfile+win)):
                scrollfile='0'
            else:
                scrollfile=self._scrollfile+win
            self.screen('-h %s -t \"%s\" %s %s %s %s %s %s' % (scrollback_len,title,winarg,self.primer,primer_arg,self.projectsdir, scrollfile,os.path.join(self.savedir,"win_"+win)) )
            #self.screen('-h %s -t \"%s\" %s %s %s %s %s %s' % (scrollback_len,title,winarg,self.primer,primer_arg,self.projectsdir,"0",os.path.join(self.savedir,"win_"+win)) )
        elif type[0]=='g':
            self.screen('-t \"%s\" %s //group' % (title,winarg ) )
        else:
            out ('%s Unknown window type "%s". Ignoring.'%(win,type))
            return -1
       
        newwin = self.number()
        return newwin
    
    def __order_group(self,newwin,pid,hostgroup,rootwindow,rootgroup,win,time,groupid,group,type,title,filter,scrollback_len,processes):
        if groupid=="-1":
            # this select is necessary in case of a group name conflict
            self.select(rootwindow)
            self.group(False,rootgroup,newwin)
        else:
            try:
                groupid=self.__wins_trans[groupid]
            except:
                pass
            # this select is necessary in case of a group name conflict
            self.select(groupid)
            self.group(False,group,newwin)
    
    def __scrollback_clean(self):
        '''clean up scrollback files: remove empty lines at the beginning and at the end of a file'''
        for f in glob.glob(os.path.join(self.basedir,self.savedir,'hardcopy.*')):
            try:
                ftmp=f+"_tmp"
                temp=open(ftmp,'w')
                thefile = open(f,'r')
                beginning=True
                for line in thefile:
                    if beginning: 
                        if cmp(line,'\n') == 0:
                            line = line.replace('\n','')
                        else:
                            beginning=False
                    temp.write(line)
                temp.close()
                thefile.close()

                temp = open( ftmp, 'r' )
                endmark=-1
                lockmark=False
                for i,line in enumerate(temp):
                    if cmp(line,'\n') == 0:
                        if not lockmark:
                            endmark=i
                            lockmark=True
                    else:
                        endmark=-1
                        lockmark=False
                temp.close()

                if endmark > 1:
                    thefile = open(f , 'w')
                    temp=open(ftmp,'r')
                    for i,line in enumerate(temp):
                        if i == endmark:
                            break;
                        else:
                            thefile.write(line)
                    thefile.close()
                    temp.close()
                    util.remove(ftmp)
                else:
                    util.remove(f)
                    os.rename(ftmp,f)
            except:
                out ('Unable to clean scrollback file: '+f)

    def __remove_all_layouts(self):
        currentlayout=0
        while currentlayout!=-1:
            self.layout('remove',False)
            self.layout('next',False)
            currentlayout,currentlayoutname=self.get_layout_number()

    def __move_all_windows(self,shift,group,kill=False):
        homewindow=int(self.homewindow)
        # create wrap group for existing windows
        self.screen('-t \"%s\" //group' % ('%s_%s'%(group,self.__unique_ident)) )
        self.group(False,'none')
        self.wrap_group_id=self.number()

        # move windows by shift and put them in a wrap group
        #for cwin,cgroupid,ctype,ctty in sc.gen_all_windows_fast(self.pid):
        for cwin,cgroupid,cgroup,ctty,ctype,ctypestr,ctitle,cfilter,cscroll,ctime in sc.gen_all_windows_full(self.pid):
            iwin=int(cwin)
            if iwin==homewindow:
                homewindow=iwin+shift
                self.homewindow=str(homewindow)
            
            cgroupid,cgroup = self.get_group(cwin)
            if cgroup=="none":
                self.select(self.wrap_group_id)
                self.group(False,group,str(cwin))
            command='%s -p %s -X number +%d' % (self.sc,cwin,shift)
            if str(cwin)==str(self.wrap_group_id):
                out('Moving wrap group %s to %d'%(cwin,iwin+shift))
                self.wrap_group_id=str(iwin+shift)
            else:
                out('Moving window %s to %d'%(cwin,iwin+shift))
            os.system(command)
        self.select('%d'%(homewindow))

    def lastmsg(self):
        return util.timeout_command('%s -Q @lastmsg' % (self.sc),self.timeout)[0]

    def command_at(self,output,command,win="-1"):
        if win=="-1":
            win=""
        else:
            win="-p %s"%win
        cmd = '%s %s -X %s'% (self.sc,win,command)
        #print ('command_at(%s): %s'%(output,cmd))
        os.system(cmd) 
        if output:
            l=self.lastmsg()
            if not l:
                return ''
            if l.startswith('C'):
                #no such window
                return -1
            else:
                return l

    def query_at(self,command,win="-1"):
        if win=="-1":
            win=""
        else:
            win="-p %s"%win
        try:
            cmd='%s %s -Q @%s'% (self.sc,win,command)
            l=util.timeout_command(cmd,self.timeout)[0] 
            if l.startswith('C'):
                #no such window
                return -1
            else:
                return l
        except:
            return None

    def get_number_and_title(self,win="-1"):
        msg=self.command_at(True, 'number',win)
        if msg==-1:
            return -1,-1
        elif msg[0]!='T': # This is window...
            return self.get_number_and_title(win)
        number,title = msg.split("(",1)
        number = number.strip().rsplit(' ',1)[1]
        title = title.rsplit(")",1)[0]
        return number,title

    def get_sessionname(self):
        return self.command_at(True, 'number',win).strip("'").split("'",1)[1]

    def tty(self,win="-1"):
        msg=self.query_at('tty',win)
        return msg

    def get_maxwin(self):
        msg=self.command_at(True, 'maxwin')
        maxwin=int(msg.split(':')[1].strip())
        return maxwin

    def maxwin(self):
        return self.get_maxwin()
    '''
    def get_info(self,win):
       
        msg=self.command_at(True, 'info',win)
        return msg
    '''
    def info(self,win="-1"):
        msg=self.query_at('info',win)
        if msg!=-1:
            r=[]
            head,tail=msg.split(' ',1)
            size1,size2=head.split('/')
            size2,size3=size2.split(')')
            size1x,size1y=size1.strip('()').split(',')
            size2x,size2y=size2.strip('()').split(',')
            flow,encoding,number_title=tail.strip().split(' ',2)
            number,title=number_title.split('(',1)
            title.strip(')')
            return  size1x,size1y,size2x,size2y,size3,flow,encoding,number,title
        else:
            return None
    
    def dinfo(self):
        msg=self.command_at(True, 'dinfo')
        msg = msg.split(' ')
        nmsg=msg.pop(0).strip('(').rstrip(')').split(',',1)
        nmsg=nmsg+msg
        return nmsg

    def echo(self,args,win="-1"):
        msg=self.query_at('echo \"%s\"'%args,win)
        return msg

    def Xecho(self,args,win="-1"):
        msg=self.command_at(False, 'echo \"%s\"'%args)

    def number(self,args='',win="-1"):
        msg=self.query_at('number %s'%args,win)
        if not args:
            return msg.split(' (',1)[0]

    def focusminsize(self,args=''):
        msg=self.command_at(True, 'focusminsize %s'%args)
        try:
            return msg.split('is ',1)[1].strip()
        except:
            return '0 0'
    
    def stuff(self,args='',win="-1"):
        self.command_at(False, 'stuff "%s"'%args,win)


    def colon(self,args='',win="-1"):
        self.command_at(False, 'colon "%s"'%args,win)
    
    def resize(self,args=''):
        self.command_at(False, 'resize %s'%args)

    def focus(self,args=''):
        self.command_at(False, 'focus %s'%args)

    def kill(self,win="-1"):
        self.command_at(False, 'kill',win)

    def idle(self,timeout,args):
        self.command_at(False , 'idle %s %s'%(timeout,args))

    def only(self):
        self.command_at(False , 'only')

    def quit(self):
        self.command_at(False , 'quit')

    def fit(self):
        self.command_at(False , 'fit')

    def layout(self,args='',output=True):
        msg=self.command_at(output, 'layout %s'%args)
        return msg

    def split(self,args=''):
        self.command_at(False , 'split %s'%args)

    def screen(self,args='',win="-1"):
        self.command_at(False , 'screen %s'%args,win)

    def scrollback(self,args='',win="-1"):
        msg=self.command_at(True, 'scrollback %s'%args,win)
        return msg.rsplit(' ',1)[1].strip()

    def source(self,args=''):
        self.command_at(False , 'source "%s"'%args)

    def select(self,args='',win="-1"):
        msg=self.query_at('select %s'%args,win)
        return msg

    def sessionname(self,args=''):
        if len(args)>0:
            name=self.command_at(True, 'sessionname').rsplit('\'',1)[0].split('\'',1)[1]
            nsessionname="%s.%s"%(name.split('.',1)[0],args)
        else:
            nsessionname=None
        msg=self.command_at(True, 'sessionname %s'%args)
        if nsessionname:
            self.pid=nsessionname
            self.set_session(self.pid)
            return nsessionname
        else:
            try:
                return msg.rsplit('\'',1)[0].split('\'',1)[1]
            except:
                return None
    def time(self,args=''):
        if args:
            args='"%s"'%args
        msg=self.query_at('time %s'%args)
        return msg

    def title(self,args='',win="-1"):
        if args:
            args='"%s"'%args
            self.command_at(False , 'title %s'%args,win)
        else:
            msg=self.query_at('title',win)
            return msg

    def windows(self):
        msg=self.query_at('windows')
        return msg

    def wipe(self,args=''):
        os.popen('screen -wipe %s'%args)

    def backtick(self,id,lifespan='',autorefresh='',args=''):
        self.command_at(False , 'backtick %s %s %s %s'%(id,lifespan,autorefresh,args))

    def get_layout_number(self):
        msg=self.command_at(True, 'layout number')
        if not msg.startswith('This is layout'):
            return -1,-1
        currentlayout,currentlayoutname = msg.split('layout',1)[1].rsplit('(')
        currentlayout = currentlayout.strip()
        currentlayoutname = currentlayoutname.rsplit(')')[0]
        return currentlayout,currentlayoutname
    
    def get_layout_new(self,name=''):
        msg=self.command_at(True, 'layout new %s'%name)
        if msg.startswith('No more'):
            return False
        else:
            return True

    def get_group(self,win="-1"):
        msg=self.command_at(True, 'group',win)
        if msg.endswith('no group'):
            group = 'none'
            groupid = '-1'
        else:
            groupid,group = msg.rsplit(")",1)[0].split(" (",1)
            groupid = groupid.rsplit(' ',1)[1]
        return groupid,group

    def group(self,output=True,args='',win="-1"):
        if args:
            args='"%s"'%args
        msg=self.command_at(output, 'group %s'%args,win)
        if output:
            if msg.endswith('no group'):
                group = 'none'
                groupid = '-1'
            else:
                groupid,group = msg.rsplit(")",1)[0].split(" (",1)
                groupid = groupid.rsplit(' ',1)[1]
            return groupid,group

    def get_exec(self,win):
        msg=self.command_at(True, 'exec',win)
        msg = msg.split(':',1)[1].strip()
        if msg.startswith('(none)'):
            return -1
        else:
            return msg


    def __save_screen(self):
        errors=[]
        homewindow=self.homewindow
        # out ("Homewindow is " + homewindow)
        group_wins={}
        group_groups={}
        excluded_wins=[]
        excluded_groups=[]
        scroll_wins=[]
        scroll_groups=[]
        cwin=-1
        ctty=None
        cppids={}
        rollback=None,None,None
        ctime=self.time()
        findir=os.path.join(self.basedir,self.savedir)
        self.command_at(False, 'at \# dumpscreen window %s'%os.path.join(self.basedir,self.savedir,"winlist"))
        self.command_at(False, 'at \# dumpscreen window %s -F'%os.path.join(self.basedir,self.savedir))
        self.command_at(False, 'hardcopydir %s'%os.path.join(self.basedir,self.savedir))
        self.command_at(False, 'at \# hardcopy -h')
        self.command_at(False, 'hardcopydir $CWD')
        try:
            f=open(os.path.join(findir,"winlist"),'r')
            f.close()
        except:
            self.command_at(False, 'at \# dumpscreen window %s'%os.path.join(self.basedir,self.savedir,"winlist"))
        fmru = open(os.path.join(findir,"mru"),"w") 
        for line in open(os.path.join(findir,"winlist"),'r'):
            try:
                id,cgroupid,ctty,ctitle = line.strip().split(' ',3)
            except:
                id,cgroupid,ctty= line.strip().split(' ')
                ctitle=None
            cwin=id
            fmru.write("%s "%cwin)
            
            if(ctty[0]=='z'): # zombie
                continue
            if(ctty[0]=="g"): # group
                ctype="group"
                cpids = None
                cpids_data=None
                if self.excluded:
                    if cwin in self.excluded or ctitle in self.excluded:
                        excluded_groups.append(cwin)
                    try:
                        group_groups[cgroupid]+=[cwin]
                    except:
                        group_groups[cgroupid]=[cwin]
                if self.scroll:
                    if cwin in self.scroll or ctitle in self.scroll:
                        scroll_groups.append(cwin)
                    try:
                        group_groups[cgroupid]+=[cwin]
                    except:
                        group_groups[cgroupid]=[cwin]
            else:
                if self.excluded:
                    if cwin in self.excluded or ctitle in self.excluded:
                        excluded_wins.append(cwin)
                    else:
                        try:
                            group_wins[cgroupid]+=[cwin]
                        except:
                            group_wins[cgroupid]=[cwin]
                if self.scroll:
                    if cwin in self.scroll or ctitle in self.scroll:
                        scroll_wins.append(cwin)
                    else:
                        try:
                            group_wins[cgroupid]+=[cwin]
                        except:
                            group_wins[cgroupid]=[cwin]
                if(ctty[0]=="t"): # telnet
                    ctype="telnet"
                    cpids = None
                    cpids_data=None
                else:
                    ctype="basic"
                    # get sorted pids in window
                    cpids=sc.get_tty_pids(ctty)
                    cpids_data=[]
                    ncpids=[]
                    for pid in cpids:
                        try:
                            pidinfo=sc.get_pid_info(pid)
                            (exehead,exetail)=os.path.split(pidinfo[1])
                            if exetail in self.blacklist:
                                blacklist=True
                            else:
                                blacklist=False
                            cpids_data.append(pidinfo+tuple([blacklist]))
                            ncpids.append(pid)
                        except:
                            errors.append('%s PID %s: Unable to access. No permission or no procfs.'%(cwin,pid))
                    cpids=ncpids
            
            if(cpids):
                for i,pid in enumerate(cpids):
                    if(cpids_data[i][3]):
                        text="BLACKLISTED"
                    else: 
                        text=""
                    l=cpids_data[i][2].split('\0')
                    jremove=[]
                    wprev=False
                    for j,w in enumerate(l):
                        if w == '-c':
                            wprev=True
                        elif wprev:
                            if w.startswith(self.primer):
                                jremove+=j,j-1
                            wprev=False
                    if jremove:
                        s=[]
                        for j,w in enumerate(l):
                            if j not in jremove:
                                s.append(w)
                        newdata=(cpids_data[i][0],cpids_data[i][1],"\0".join(["%s"%v for v in s]),cpids_data[i][3])
                        cpids_data[i]=newdata

                    #out('%s    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (text,pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))
                    vim_name=str(None)
                    args=cpids_data[i][2].split('\0')
                    if args[0].endswith(self.primer_base) and args[1]=='-p':
                        sys.stdout.write('(primer)')
                        rollback=self.__rollback(cpids_data[i][2])
                        #out(str(rollback))
                    elif args[0] in self.vim_names and self.bVim:
                        sys.stdout.write('(vim)')
                        vim_name=self.__save_vim(id)
                        nargs=[]
                        rmarg=False
                        for arg in args:
                            if rmarg:
                                rmarg=False
                                pass
                            elif arg in ('-S','-i'):
                                rmarg=True
                            else:
                                nargs.append(arg)
                        args=nargs
                        newdata=(cpids_data[i][0],cpids_data[i][1],"\0".join(["%s"%v for v in args]),cpids_data[i][3])
                        cpids_data[i]=newdata
                    
                    cpids_data[i]=(cpids_data[i][0],cpids_data[i][1],cpids_data[i][2],cpids_data[i][3],vim_name)
            scrollback_filename=os.path.join(self.basedir,self.savedir,"hardcopy."+id)
            sys.stdout.write("%s %s | "%(cwin,ctype))
            errors+=self.__save_win(id,ctype,cpids_data,ctime,rollback)
            rollback=None,None,None
        out('')
        fmru.close()
        util.remove(os.path.join(findir,"winlist"))
        # remove ignored scrollbacks
        if 'all' in self.scroll:
            for f in glob.glob(os.path.join(self.basedir, self.savedir, "hardcopy.*")):
                open(f,'w')
        elif self.scroll:
            scroll_groups_tmp=[]
            while scroll_groups:
                sgroup=scroll_groups.pop()
                if sgroup not in scroll_groups_tmp:
                    scroll_groups_tmp.append(sgroup)
                try:
                    ngroups = group_groups[sgroup]
                    if ngroups:
                        for g in ngroups:
                            scroll_groups.append(g)
                except:
                    pass
            scroll_groups = scroll_groups_tmp
            out('Scrollback excluded groups: %s'%str(scroll_groups))
            for sgroup in scroll_groups:
                scroll_wins.append(sgroup)
                try:
                    for w in group_wins[sgroup]:
                        scroll_wins.append(w)
                except:
                    pass
            out('All scrollback excluded windows: %s'%str(scroll_wins))
            for w in scroll_wins:
                util.remove(os.path.join(self.basedir, self.savedir, "hardcopy.%s"%w))
        # remove ignored windows
        if self.excluded:
            excluded_groups_tmp=[]
            while excluded_groups:
                egroup=excluded_groups.pop()
                if egroup not in excluded_groups_tmp:
                    excluded_groups_tmp.append(egroup)
                try:
                    ngroups = group_groups[egroup]
                    if ngroups:
                        for g in ngroups:
                            excluded_groups.append(g)
                except:
                    pass
            excluded_groups = excluded_groups_tmp
            out('Excluded groups: %s'%str(excluded_groups))
            for egroup in excluded_groups:
                excluded_wins.append(egroup)
                try:
                    for w in group_wins[egroup]:
                        excluded_wins.append(w)
                except:
                    pass
            out('All excluded windows: %s'%str(excluded_wins))
            bpath1 = os.path.join(self.basedir, self.savedir, "win_")
            bpath2 = os.path.join(self.basedir, self.savedir, "hardcopy.")
            bpath3 = os.path.join(self.basedir, self.savedir, "vim_W")
            for win in excluded_wins:
                util.remove(bpath1+win)
                util.remove(bpath2+win)
                for f in glob.glob(bpath3+win+'_*'):
                    util.remove(f)

        linkify(os.path.join(self.basedir,self.savedir),"win_"+homewindow,"last_win")
        if errors:
            out('Errors:')
            for error in errors:
                out(error)
        out('\nSaved: '+str(ctime))
        
    def __restore_mru(self):
        try:
            mru=open(os.path.join(self.basedir,self.savedir,"mru"),'r').read().strip().split(' ')
            mru.reverse()
            for win in mru:
                self.select("%s"%self.__wins_trans[win])
        except:
            out('Unable to restore MRU!')
            pass
        if self.restore_previous:
            self.select(self.homewindow)
        #elif self.__layouts_loaded:
        #    pass
        elif os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            # select last selected window
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            try:
                self.select(self.__wins_trans[lastid])
            except:
                self.select('-')
        else:
            self.select('-')

    def __rollback(self,cmdline):
        try:
            cmdline=cmdline.split('\0')
            requireme(self.homedir,cmdline[2], cmdline[3],True)
            path=os.path.join(self.homedir,cmdline[2],cmdline[4])
            fhead,ftail=os.path.split(cmdline[4])
            target=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            number=ftail.split('_')[1]
            oldsavedir=fhead
            
            # import win_* files
            try:
                shutil.move(os.path.join(self.homedir,cmdline[2],cmdline[4]),target)
            except Exception,e:
                out(str(e))
                target=None
                pass
            
            # import hardcopy.* files
            fhead,ftail=os.path.split(cmdline[3])
            target2=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            try:
                shutil.move(os.path.join(self.homedir,cmdline[2],cmdline[3]),target2)
            except Exception,e:
                out(str(e))
                target2=None
                pass

            if os.path.isfile(target):
                # fhead is savefile base name
                return (target,target2,os.path.join(self.homedir,cmdline[2],fhead))
            else:
                return (None,None,None)
        except:
            return (None,None,None)
        

    def __load_layouts(self):
        cdinfo=map(int,self.dinfo()[0:2])
        out('Terminal size: %s %s'%(cdinfo[0],cdinfo[1]))
        homewindow=self.homewindow
        homelayout,homelayoutname=self.get_layout_number()
        layout_trans={}
        layout_c=len(glob.glob(os.path.join(self.basedir,self.savedir,'layout_*')))
        if layout_c > 0:
            self.__layouts_loaded=True
        lc=0
        while lc < layout_c:
            filename=None
            try:
                try:
                    filename=glob.glob(os.path.join(self.basedir,self.savedir,'layout_%d_*'%lc))[0]
                    layoutname=filename.split('_',2)[2]
                    layoutnumber=filename.split('_',2)[1]
                    status=self.get_layout_new(layoutname)
                    if not status:
                        out('Maximum number of layouts reached. Ignoring layout %s (%s).'%(layoutnumber,layoutname))
                        break
                    else:
                        currentlayout,currentlayoutname=self.get_layout_number()
                        
                        layout_trans[layoutnumber]=currentlayout

                        self.source(filename)
                        (head,tail)=os.path.split(filename)
                        
                        filename2=os.path.join(head,"win"+tail) #read winlayout
                        focus_offset=0
                        f=open(filename2,'r')
                        dinfo=map(int,f.readline().split(" "))
                        focusminsize=f.readline()
                        regions_size=[]
                        winlist=[]
                        focus_offset=0
                        for i,line in enumerate(f):
                            try:
                                if line[0]=='f':
                                    focus_offset,window,sizex,sizey=line.strip().split(' ')
                                    focus_offset=i
                                else:
                                    window,sizex,sizey=line.strip().split(' ')
                            except:
                                try:
                                    region_c=line.strip()
                                except:
                                    pass
                                break
                            winlist.append(window)
                            nsizex=(int(sizex)*cdinfo[0])/dinfo[0]
                            nsizey=(int(sizey)*cdinfo[1])/dinfo[1]
                            regions_size.append((nsizex,nsizey))
                            if not window=="-1":
                                try:
                                    # __wins_trans may be incomplete
                                    self.select("%s"%self.__wins_trans[window])
                                except:
                                    out('Unable to set focus for: %s'%window)
                            self.focus()
                        f.close()

                        # set region dimensions
                        self.focus('top')
                        out("%s (%s) : regions : %s(%s) %s - %s"%(layoutnumber,layoutname,region_c,focus_offset,winlist,regions_size))
                        for size in regions_size:
                            if size[0]>0:
                                self.resize('-h %d'%(size[0]))
                                self.resize('-v %d'%(size[1]))
                                self.fit()

                            self.focus()
                        
                        # restore focus on the right region
                        self.select_region(focus_offset)

                        self.focusminsize(focusminsize)
                except:
                    layout_c+=1
            finally:
                lc+=1

        # select last layout
        lastname=None
        lastid_l=None

        if homelayout!=-1:
            out("Returning homelayout %s"%homelayout)
            self.layout('select %s'%homelayout,False)
        else:
            out('No homelayout - unable to return.')
        
        if not self.restore_previous:
            if os.path.exists(os.path.join(self.basedir,self.savedir,"last_layout")) and len(layout_trans)>0:
                last=os.readlink(os.path.join(self.basedir,self.savedir,"last_layout"))
                (lasthead,lasttail)=os.path.split(last)
                last=lasttail.split("_",2)
                lastname=last[2]
                lastid_l=last[1]
                self.layout('select %s'%layout_trans[lastid_l],False)
                # ^^ layout numbering may change, use layout_trans={}
            
    def select_region(self,region):
        self.focus('top')
        for i in range(0,region):
            self.focus()

    def __save_layouts(self):
        homelayout,homelayoutname=self.get_layout_number()
        layoutname=homelayoutname
        
        if homelayout==-1:
            out("No layouts to save. Create layouts with \":layout new\"")
            return False
        currentlayout=homelayout

        loop_exit_allowed=False
        while currentlayout!=homelayout or not loop_exit_allowed:
            loop_exit_allowed=True
            sys.stdout.write("%s(%s); "%(currentlayout,layoutname))
            self.command_at(False,'eval \'layout dump \"%s\"\' \'dumpscreen layout \"%s\"\' \'layout next\''%(os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname),os.path.join(self.basedir,self.savedir,"winlayout_"+currentlayout+"_"+layoutname)))
            currentlayout,layoutname=self.get_layout_number()
        
        linkify(os.path.join(self.basedir,self.savedir),"layout_"+homelayout+"_"+homelayoutname,"last_layout")
        
        return True

    def __save_vim(self,winid):
        name="vim_W%s_%s"%(winid,self.__unique_ident)
        fname=os.path.join(self.basedir,self.savedir,name)
        cmd = '^[^[:silent call histdel(\':\',-1) | mksession %s | wviminfo %s\n'%(fname+'_session',fname+'_info')
        self.stuff(cmd, winid)
        # undo files are useless if the target file changes even a single bit
        # self.stuff(":bufdo exec 'wundo! %s'.expand('%%')\n"%(fname+'_undo_'), winid)
        return name
           
    def __save_win(self,winid,ctype,pids_data,ctime,rollback):
        errors=[]
        fname=os.path.join(self.basedir,self.savedir,"win_"+winid)
        if rollback[1]:
            #time=linecache.getline(rollback[0],2).strip()
            #copy scrollback
            shutil.move(rollback[1],os.path.join(self.basedir,self.savedir,"hardcopy."+winid))

        basedata_len=7

        f=open(fname,"a")
        if rollback[0]:
            rollback_dir=rollback[2]
            target=rollback[0]
            fr=open(target,'r')
            last_sep=1
            for i,line in enumerate(fr.readlines()[basedata_len:]):
                f.write(line)
                if line=='-\n':
                    last_sep=i
                elif i-last_sep==6 and line.startswith('vim_'):
                    #import vim files but update the window number in filename
                    for filename in glob.glob(os.path.join(rollback_dir,line.strip()+'_*')):
                        try:
                            tvim="vim_W%s_%s"%(winid,os.path.basename(filename).split('_',2)[2])
                            tvim=os.path.join(self.basedir,self.savedir,tvim)
                            shutil.move(filename,tvim)
                        except:
                            errors.append('Unable to rollback vim: %s'%filename)
            util.remove(target)
        else:
            pids_data_len="0"
            if(pids_data):
                pids_data_len=str(len(pids_data))
            f.write(pids_data_len+'\n')
            if(pids_data):
                for pid in pids_data:
                    f.write("-\n")
                    for i,data in enumerate(pid):
                        if i == 2:
                            if data.endswith('\0\0'):
                                data=data[:len(data)-1]
                            f.write(str(len(data.split('\0'))-1)+'\n')
                            f.write(str(data)+'\n')
                        else:
                            f.write(str(data)+'\n')
                f.write(ctime)
        f.close()
        return errors

    def __setup_savedir(self,basedir,savedir):
        out ("Setting up session directory %s" % savedir)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
            f=open(os.path.join(basedir,self.blacklistfile),'w')
            f.close()

        if os.path.exists(os.path.join(basedir,savedir)):
            out("Directory \"%s\" in \"%s\" already exists. Use --force to overwrite." % (savedir, basedir))
            if self.force:
                out('forcing..')
                out('cleaning up \"%s\"' % savedir)
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'win_*')))
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'hardcopy.*')))
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'layout_*')))
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'winlayout_*')))
                return True
            else:
                out('Aborting.')
                return False
        else:
            os.makedirs(os.path.join(basedir,savedir))
            return True

