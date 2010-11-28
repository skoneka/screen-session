
import subprocess,sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,linecache

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
    procdir="/proc"
    MAXWIN=-1
    MAXWIN_REAL=-1
    MINWIN_REAL=0
    force=False
    lastlink="last"
    enable_layout = False
    restore_previous = False
    exact=False
    bVim=True
    group_other='OTHER_WINDOWS'
    homewindow=""
    sc=None
    wrap_group_id=None
    
    primer="screen-session-primer"
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

    def __init__(self,pid,projectsdir='/dev/null',savedir='/dev/null'):
        self.homedir=os.path.expanduser('~')
        self.projectsdir=str(projectsdir)
        self.basedir=os.path.join(self.homedir,self.projectsdir)
        self.savedir=str(savedir)
        self.pid=str(pid)
        self.set_session(self.pid)
        self.primer=os.path.join(os.path.dirname(sys.argv[0]),self.primer)

    def set_session(self,sessionname):
        self.sc='%s -S %s'%(which('screen')[0],sessionname)
        self.__unique_ident="%s_%s"%(sessionname.split('.',1)[0],time.strftime("%y%m%d_%H%M%S"))

    def save(self):
        self.homewindow,title=self.get_number_and_title()
        out("\n======CREATING___DIRECTORIES======")
        if not self.__setup_savedir(self.basedir,self.savedir):
            return False
        out("\n======SAVING___SCREEN___SESSION======")
        self.__save_screen()
        
        if self.enable_layout:
            out("\n======SAVING___LAYOUTS======")
            self.homewindow_last,title=self.get_number_and_title()
            self.__save_layouts()
        out("\n======CLEANUP======")
        self.__scrollback_clean()
        return True

    def load(self):
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
            return False

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
            out('Moving windows...')
            self.__move_all_windows(maxnewwindow+1,self.group_other,False)
        
        self.homewindow=self.number()
        out("\n======LOADING___SCREEN___SESSION======")
        self.__load_screen()
        if self.enable_layout:
            out("\n======LOADING___LAYOUTS======")
            self.__load_layouts()
        return True

    def exists(self):
        msg=self.echo('test')
        try:
            if msg.startswith('No'): # 'No screen session found'
                return False
            else:
                return True
        except:
            return False

    def __remove_and_escape_bad_chars(self,str):
        # some characters are causing problems when setting window titles
        return str.replace('\\','\\\\\\\\').replace('|','I')# how to properly escape "|"?

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
            os.system('%s -X screen -t \"%s\" %s //group' % (self.sc,rootgroup,0 ) )
            os.system('%s -X group \"%s\"' % (self.sc,hostgroup) )
        
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
                    wins.append((win[0], win[1], win[2], win[3], self.__remove_and_escape_bad_chars(win[4]), win[5], win[6],win[7]))
            except:
                out('%s Unable to load window'%id)

        for win,time,group,type,title,filter,scrollback_len,processes in wins:
            self.__wins_trans[win]=self.__create_win(self.exact,self.__wins_trans,self.pid,hostgroup,rootgroup,win,time,group,type,title,filter,scrollback_len,processes)
        
        for win,time,group,type,title,filter,scrollback_len,processes in wins:
            groupid,group=group.split(' ',1)
            self.__order_group(self.__wins_trans[win],self.pid,hostgroup,rootwindow,rootgroup,win,time,groupid,group,type,title,filter,scrollback_len,processes)
        
        out ("Rootwindow is "+rootwindow)
        self.select(rootwindow)
        
        # select last selected window
        lastid=''
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            self.lastid=lasttail.split("_",1)[1]
            self.select_last_window()
        
        # out ("Returning homewindow " +homewindow)
        self.select(homewindow)
       
        if not self.restore_previous:
            self.select_last_window()

    def select_last_window(self):
        try:
            #out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[self.lastid],self.lastid))
            self.select(self.__wins_trans[self.lastid])
        except:
            self.select('-')
            

    # Take a list of string objects and return the same list
    # stripped of extra whitespace.
    def __striplist(self,l):
        return([x.strip() for x in l])


    def __create_win(self,keep_numbering,wins_trans,pid,hostgroup,rootgroup,win,time,group,type,title,filter,scrollback_len,processes):
        if keep_numbering:
            winarg=win
        else:
            winarg=""
        
        if type=='basic':
            os.system('screen -S %s -X screen -h %s -t \"%s\" %s %s %s %s %s %s' % (pid,scrollback_len,title,winarg,self.primer,self.primer_arg,self.projectsdir,os.path.join(self.savedir,"scrollback_"+win),os.path.join(self.savedir,"win_"+win)) )
        elif type=='group':
            os.system('screen -S %s -X screen -t \"%s\" %s //group' % (pid,title,winarg ) )
        else:
            out ('%s Unknown window type "%s". Ignoring.'%(win,type))
            return -1
       
        newwin = self.number()
        return newwin
    
    def __order_group(self,newwin,pid,hostgroup,rootwindow,rootgroup,win,time,groupid,group,type,title,filter,scrollback_len,processes):
        if groupid=="-1":
            self.select(rootwindow)
            os.system('screen -S %s -X at %s group %s' % (pid,newwin,rootgroup) )
        else:
            try:
                groupid=self.__wins_trans[groupid]
            except:
                pass
            self.select(groupid)
            os.system('screen -S %s -X at %s group %s' % (pid,newwin,group) )
    
    def __scrollback_clean(self):
        '''clean up scrollback files: remove empty lines at the beginning and at the end of a file'''
        for f in self.__scrollbacks:
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
                else:
                    os.remove(f)
                    os.rename(ftmp,f)
            except:
                out ('Unable to clean scrollback file: '+f)

    def __remove_all_layouts(self):
        currentlayout=0
        while currentlayout!=-1:
            self.layout('remove')
            self.layout('next')
            currentlayout,currentlayoutname=self.get_layout_number()

    def __kill_windows(self,kill_list):
        #kill_list.pop(len(kill_list)-1)
        for w in kill_list:
            number,title=self.get_number_and_title(w)
            out('killing: '+str(w)+ ':'+number+':'+title)
            os.system('%s -X at %s kill' % (self.sc, w) )
    def kill_old_windows(self):
        out ('killing: '+str(self.__kill_list))
        self.__kill_windows(self.__kill_list)


    def __move_all_windows(self,shift,group,kill=False):
        homewindow=int(self.homewindow)
        cwin=-1
        ctty=None
        cppids={}
        searching=False

        if self.MAXWIN>0:
            r=range(0,self.MAXWIN+1)
            
            # create wrap group for existing windows
            os.system('%s -X screen -t \"%s\" //group' % (self.sc,group) )
            os.system('%s -X group %s' % (self.sc, 'none') )
            cwin=int(self.number())
            self.wrap_group_id=str(cwin+shift)
            self.number(self.wrap_group_id)
            group=group+'_'+self.__unique_ident
            self.title(group)
            if cwin not in r:
                r.append(cwin)
            r.sort()
            r.reverse()
            # move windows by shift and put them in a wrap group
            for i in r:
                cselect = self.select(i)
                if cselect:
                    #no such window
                    if searching:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    else:
                        msg='Searching for windows (set --maxwin)...'
                        sys.stdout.write('\n'+msg)
                        self.echo(msg)
                        searching=True
                else:
                    if(searching):
                        searching=False
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                    cwin=int(self.number())
                    if cwin==homewindow:
                        homewindow=cwin+shift
                    
                    cgroupid,cgroup = self.get_group(cwin)
                    if cgroup=="none":
                        self.select(self.wrap_group_id)
                        self.group(group,str(cwin))
                    command='%s -p %d -X number +%d' % (self.sc,cwin,shift)
                    out('Moving window %d to %d'%(cwin,cwin+shift))
                    os.system(command)
                    # after moving or kill window number changes so have to update cwin
                    cwin=int(self.number())

        self.select('%d'%(homewindow))

    def lastmsg(self):
        try:
            return util.timeout_command('%s -Q @lastmsg' % (self.sc),self.timeout)[0]
        except:
            return ''

    def command_at(self,command,win="-1"):
        if win=="-1":
            win=""
        else:
            win="-p %s"%win
        #print('%s %s -X %s'% (self.sc,win,command))
        os.system('%s %s -X %s'% (self.sc,win,command)) 
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
            l=util.timeout_command('%s %s -Q @%s'% (self.sc,win,command),self.timeout)[0] 
            if l.startswith('C'):
                #no such window
                return -1
            else:
                return l
        except:
            return None

    def get_number_and_title(self,win="-1"):
        msg=self.command_at('number',win)
        if msg==-1:
            return -1,-1
        number,title = msg.split("(",1)
        number = number.strip().rsplit(' ',1)[1]
        title = title.rsplit(")",1)[0]
        return number,title

    def get_sessionname(self):
        return self.command_at('number',win).strip("'").split("'",1)[1]

    def tty(self,win="-1"):
        msg=self.query_at('tty',win)
        return msg

    def get_maxwin(self):
        msg=self.command_at('maxwin')
        maxwin=int(msg.split(':')[1].strip())
        return maxwin

    def maxwin(self):
        return self.get_maxwin()
    '''
    def get_info(self,win):
       
        msg=self.command_at('info',win)
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
    def get_regionsize(self,win="-1"):
        msg=self.command_at('regionsize',win)
        return msg.split(' ')
    
    def dinfo(self):
        msg=self.command_at('dinfo')
        msg = msg.split(' ')
        nmsg=msg.pop(0).strip('(').rstrip(')').split(',',1)
        nmsg=nmsg+msg
        return nmsg

    def echo(self,args,win="-1"):
        msg=self.query_at('echo \"%s\"'%args,win)
        return msg

    def number(self,args='',win="-1"):
        msg=self.query_at('number %s'%args,win)
        if not args:
            return msg.split(' (',1)[0]

    def focusminsize(self,args=''):
        msg=self.command_at('focusminsize %s'%args)
        try:
            return msg.split('is ',1)[1].strip()
        except:
            return '0 0'
    
    def stuff(self,args='',win="-1"):
        msg=self.command_at('stuff "%s"'%args,win)


    def colon(self,args='',win="-1"):
        msg=self.command_at('colon "%s"'%args,win)
    
    def resize(self,args=''):
        msg=self.command_at('resize %s'%args)

    def focus(self,args=''):
        msg=self.command_at('focus %s'%args)

    def kill(self,win="-1"):
        msg=self.command_at('kill',win)
        return msg

    def idle(self,timeout,args):
        msg=self.command_at('idle %s %s'%(timeout,args))

    def only(self):
        self.command_at('only')

    def quit(self):
        msg=self.command_at('quit')

    def fit(self):
        msg=self.command_at('fit')

    def layout(self,args=''):
        msg=self.command_at('layout %s'%args)
        return msg

    def split(self,args=''):
        msg=self.command_at('split %s'%args)

    def screen(self,args='',win="-1"):
        msg=self.command_at('screen %s'%args,win)
        return msg

    def scrollback(self,args='',win="-1"):
        msg=self.command_at('scrollback %s'%args,win)
        return msg.rsplit(' ',1)[1].strip()

    def source(self,args=''):
        msg=self.command_at('source "%s"'%args)
        return msg

    def select(self,args='',win="-1"):
        msg=self.query_at('select %s'%args,win)
        return msg

    def sessionname(self,args=''):
        if len(args)>0:
            name=self.command_at('sessionname').rsplit('\'',1)[0].split('\'',1)[1]
            nsessionname="%s.%s"%(name.split('.',1)[0],args)
        else:
            nsessionname=None
        msg=self.command_at('sessionname %s'%args)
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
            msg=self.command_at('title %s'%args,win)
        else:
            msg=self.query_at('title',win)
            return msg

    def windows(self):
        msg=self.query_at('windows')
        return msg

    def wipe(self,args=''):
        os.popen('screen -wipe %s'%args)

    def backtick(self,id,lifespan='',autorefresh='',args=''):
        msg=self.command_at('backtick %s %s %s %s'%(id,lifespan,autorefresh,args))

    def get_layout_number(self):
        msg=self.command_at('layout number')
        if not msg.startswith('This is layout'):
            return -1,-1
        currentlayout,currentlayoutname = msg.split('layout',1)[1].rsplit('(')
        currentlayout = currentlayout.strip()
        currentlayoutname = currentlayoutname.rsplit(')')[0]
        return currentlayout,currentlayoutname
    
    def get_layout_new(self,name=''):
        msg=self.command_at('layout new %s'%name)
        if msg.startswith('No more'):
            return False
        else:
            return True

    def get_group(self,win="-1"):
        msg=self.command_at('group',win)
        if msg.endswith('no group'):
            group = 'none'
            groupid = '-1'
        else:
            groupid,group = msg.rsplit(")",1)[0].split(" (",1)
            groupid = groupid.rsplit(' ',1)[1]
        return groupid,group

    def group(self,args='',win="-1"):
        msg=self.command_at('group %s'%args,win)
        if msg.endswith('no group'):
            group = 'none'
            groupid = '-1'
        else:
            groupid,group = msg.rsplit(")",1)[0].split(" (",1)
            groupid = groupid.rsplit(' ',1)[1]
        return groupid,group

    def get_exec(self,win):
        msg=self.command_at('exec',win)
        msg = msg.split(':',1)[1].strip()
        if msg.startswith('(none)'):
            return -1
        else:
            return msg


    def __save_screen(self):
        homewindow=self.homewindow
        # out ("Homewindow is " + homewindow)
        group_wins={}
        group_groups={}
        excluded_wins=[]
        excluded_groups=[]
        cwin=-1
        ctty=None
        cppids={}
        searching=False
        rollback=None,None,None
        ctime=self.time()
        out('NUM, GROUP, TYPE, TITLE, FILTER, SCROLLBACK')
        for i in range(0,self.MAXWIN+1):
            id=str(i)
            cwin,ctitle=self.get_number_and_title(id)
            if (cwin==-1):
                #no such window
                if searching:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                else: 
                    sys.stdout.write('Searching for windows (set --maxwin)...')
                    searching=True
            else:
                if(searching):
                    searching=False
                    sys.stdout.write('\n')
                    sys.stdout.flush()

                # has to follow get_number_and_title() to recognize zombie windows
                ctty = self.tty(id) 
                if not ctty:
                    out('%s is a zombie window. Ignoring.'%(cwin))
                    ctype="zombie"
                    continue;

                cfilter = self.get_exec(id)
                cscrollback_len = self.scrollback('',id)
                cgroupid,cgroup = self.get_group(id)
                
                # display some output
                if cfilter!=-1:
                    out('filter: exec %s'%(cfilter))
                else:
                    cfilter='-1'

                if(ctty=="group"):
                    ctype="group"
                    cpids = None
                    cpids_data=None
                    if self.excluded:
                        if cwin in self.excluded:
                            excluded_groups.append(cwin)
                        try:
                            group_groups[cgroupid]+=[cwin]
                        except:
                            group_groups[cgroupid]=[cwin]
                else:
                    if self.excluded:
                        if cwin in self.excluded:
                            excluded_wins.append(cwin)
                        else:
                            try:
                                group_wins[cgroupid]+=[cwin]
                            except:
                                group_wins[cgroupid]=[cwin]
                    if(ctty=="telnet"):
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
                            except OSError:
                                out('%s: Unable to access. No permission or no procfs.'%pid)
                        cpids=ncpids
                
                if(cpids):
                    for i,pid in enumerate(cpids):
                        if(cpids_data[i][3]):
                            text="BLACKLISTED"
                        else: 
                            text=""
                        if self.primer in cpids_data[i][2]:
                            # clean zsh -c 'primer..' by removing '-c' 'primer..'
                            l=cpids_data[i][2].split('\0')
                            if l[1]=='-c' and l[2].startswith(self.primer) and l[3]==self.primer_arg:
                                s=str(l[0])+'\0'
                                for j in range(3,len(l)):
                                    s+=str(l[j])+'\0'
                                newdata=(cpids_data[i][0],cpids_data[i][1],s,cpids_data[i][3])
                                cpids_data[i]=newdata

                        #out('%s    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (text,pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))
                        vim_name=str(None)
                        args=cpids_data[i][2].split('\0')
                        if self.primer==args[0]:
                            sys.stdout.write('Import : ')
                            rollback=self.__rollback(cpids_data[i][2])
                            #out(str(rollback))
                        elif args[0] in self.vim_names and self.bVim:
                            vim_name=self.__save_vim(cwin)
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
                scrollback_filename=os.path.join(self.basedir,self.savedir,"scrollback_"+cwin)
                if not rollback[1]:
                    # save scrollback
                    os.system('%s -X at %s hardcopy -h %s' % (self.sc, cwin, scrollback_filename) )
                    self.__scrollbacks.append(scrollback_filename)

                if ctype!="zombie":
                    self.__save_win(cwin,ctime,cgroupid,cgroup,ctype,ctitle,cfilter,cpids_data,rollback,scrollback_filename,cscrollback_len)
                rollback=None,None,None

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
            out('\nExcluded groups: %s'%str(excluded_groups))
            for egroup in excluded_groups:
                excluded_wins.append(egroup)
                try:
                    for w in group_wins[egroup]:
                        excluded_wins.append(w)
                except:
                    pass
            out('All excluded windows: %s'%str(excluded_wins))
            bpath = os.path.join(self.basedir, self.savedir, "win_")
            for win in excluded_wins:
                try:
                    os.remove(bpath+win)
                except:
                    pass

        linkify(os.path.join(self.basedir,self.savedir),"win_"+homewindow,"last_win")
        out('\nsaved on '+str(ctime))
    
    def __rollback(self,cmdline):
        try:
            cmdline=cmdline.split('\0')
            requireme(self.homedir,cmdline[2], cmdline[3],True)
            path=os.path.join(self.homedir,cmdline[2],cmdline[4])
            fhead,ftail=os.path.split(cmdline[4])
            target=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            
            number=ftail.split('_')[1]
            oldsavedir=fhead
            
            try:
                shutil.move(os.path.join(self.homedir,cmdline[2],cmdline[4]),target)
            except Exception,e:
                out(str(e))
                target=None
                pass
            
            fhead,ftail=os.path.split(cmdline[3])
            target2=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            try:
                shutil.move(os.path.join(self.homedir,cmdline[2],cmdline[3]),target2)
            except Exception,e:
                out(str(e))
                target2=None
                pass

            if os.path.isfile(target):
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
        for i in range(0,layout_c):
            filename=glob.glob(os.path.join(self.basedir,self.savedir,'layout_%d_*'%i))[0]
            layoutname=filename.split('_',2)[2]
            layoutnumber=filename.split('_',2)[1]
            stat=self.get_layout_new(layoutname)
            if not stat:
                out('Maximum number of layouts reached. Ignoring layout %s (%s)'%(layoutnumber,layoutname))
            else:
                currentlayout,currentlayoutname=self.get_layout_number()
                
                layout_trans[layoutnumber]=currentlayout

                self.source(filename)
                (head,tail)=os.path.split(filename)
                
                filename2=os.path.join(head,"win"+tail) #read winlayout
                f=open(filename2,'r')
                focus_offset=int(f.readline())
                dinfo=map(int,f.readline().split(" "))
                focusminsize=f.readline()
                regions_size=[]
                winlist=[]
                for line in f:
                    window,sizex,sizey=line.split(' ')
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
                out("%s (%s) : regions : %s - %s"%(layoutnumber,layoutname,winlist,regions_size))
                for size in regions_size:
                    if size[0]>0:
                        self.resize('-h %d'%(size[0]))
                        self.resize('-v %d'%(size[1]))
                        self.fit()

                    self.focus()

                
                # restore focus on the right region
                self.select_region(focus_offset)

                self.focusminsize(focusminsize)




        # select last layout
        lastname=None
        lastid_l=None
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_layout")) and len(layout_trans)>0:
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_layout"))
            (lasthead,lasttail)=os.path.split(last)
            last=lasttail.split("_",2)
            lastname=last[2]
            lastid_l=last[1]
            #out("Selecting last layout %s (%s) [ previously %s ]"%(layout_trans[lastid_l],lastname,lastid_l))
            self.layout('select %s'%layout_trans[lastid_l])
            # ^^ layout numbering may change, use layout_trans={}

        if homelayout!=-1:
            out("Returning homelayout %s"%homelayout)
            self.layout('select %s'%homelayout)
        else:
            out('No homelayout - unable to return.')
        
        if not self.restore_previous:
            try:
                #out("Selecting last layout %s (%s) [ previously %s ]"%(layout_trans[lastid_l],lastname,lastid_l))
                self.layout('select %s'%layout_trans[lastid_l])
            except:
                pass
        
        # select last selected window
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            self.lastid=lasttail.split("_",1)[1]
            self.select_last_window()
        
        # out ("Returning homewindow " +homewindow)
        self.select(homewindow)
       
        if not self.restore_previous:
            self.select_last_window()
            
    def select_region(self,region):
        self.focus('top')
        for i in range(0,region):
            self.focus()

    def __terminate_processes(self,ident):
        #get list of subprograms and finish them all
        procs=subprocess.Popen('ps x |grep "%s"' % (ident), shell=True, stdout=subprocess.PIPE).communicate()[0]
        procs=procs.split('\n')
        nprocs=[]
        for p in procs:
            nprocs.append(p.strip().split(' ')[0])
        procs=nprocs
        
        for p in procs:
            try:
                os.kill(int(p),signal.SIGTERM)
            except:
                pass

    __get_focus_offset_c=0
    def get_focus_offset(self):
        focus_offset=0
        cnum=self.number()
        os.system('%s -X screen %s -m %d-%d'%(self.sc,self.primer,os.getpid(),self.__get_focus_offset_c))
        #ident="%s -m %d-%d" %(self.primer,os.getpid(),self.__get_focus_offset_c)
        self.__get_focus_offset_c+=1
        markertty = self.tty()
        markernum,markertitle=self.get_number_and_title()
        #out('markernum=%s; title=%s;'%(markernum,markertitle))
        self.focus('top')


        while True:
            ctty = self.tty()
            if ctty==markertty:
                break
            else:
                self.focus()
                focus_offset+=1
        #self.__terminate_processes(ident)
        self.kill(markernum)
        self.select(cnum)
        return focus_offset

    def __save_layouts(self):
        homelayout,homelayoutname=self.get_layout_number()
        layoutname=homelayoutname
        
        if homelayout==-1:
            out("No layouts to save. Create layouts with \":layout new\"")
            return False
        dinfo=self.dinfo()
        out('Terminal size: %s %s'%(dinfo[0],dinfo[1]))
        out("Homelayout is %s (%s)"% (homelayout,homelayoutname))
        currentlayout=homelayout
        out('NUM : NREGIONS; OFFSET; (FOCUSMINSIZE); (NAME); [REGIONS]')

        loop_exit_allowed=False
        while currentlayout!=homelayout or not loop_exit_allowed:
            loop_exit_allowed=True
            cfocusminsize=self.focusminsize()
            self.focusminsize('0 0')
            self.layout('dump \"%s\"'%os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname))
            region_c = int(subprocess.Popen('grep -c "split" %s' % (os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip())+1
            focus_offset=self.get_focus_offset()
            self.focus('top')
            win=[]
            for i in range(0,region_c):
                currentnumber=self.number()
                windows = self.windows()
                csize=self.get_regionsize(currentnumber)
                offset=0
                findactive=False
                wnums,wactive=sc.parse_windows(windows)
                #out('cnum='+currentnumber.strip()+'; wactive='+str(wactive))
                #out (windows)
                if wactive==-1:
                    findactive=False
                else:
                    findactive=True

                if not findactive:
                    currentnumber="-1"
                sizex=int(csize[0])
                sizey=int(csize[1])
                win.append("%s %d %d"%(currentnumber,sizex+1,sizey+1))
                self.focus()
            out("%s : %d; %s; (%s); (%s); %s" % (currentlayout,region_c,focus_offset,cfocusminsize,layoutname,win))

            f=open(os.path.join(self.basedir,self.savedir,"winlayout_"+currentlayout+"_"+layoutname),"w")
            f.write("%d\n"%focus_offset)
            f.write("%s %s\n"%(dinfo[0],dinfo[1]))
            f.write("%s\n"%cfocusminsize)
            for w in win:
                f.write(w+'\n')
            f.close()
            
            #get back to originally focused window
            self.select_region(focus_offset)

            self.focusminsize(cfocusminsize)
            self.layout('next')
            currentlayout,layoutname=self.get_layout_number()
        
        linkify(os.path.join(self.basedir,self.savedir),"layout_"+homelayout+"_"+homelayoutname,"last_layout")
        
        out("Returned homelayout %s (%s)"% (homelayout,homelayoutname))
        
        self.select(self.homewindow_last)

        return True

    def __save_vim(self,winid):
        name="vim_%s_%s"%(self.__unique_ident,winid)
        fname=os.path.join(self.basedir,self.savedir,name)
        cmd = '^[^[:mksession %s | wviminfo %s\n'%(fname+'_session',fname+'_info')
        self.stuff(cmd, winid)
        # undo files are useless if the target file changes even a single bit
        # self.stuff(":bufdo exec 'wundo! %s'.expand('%%')\n"%(fname+'_undo_'), winid)
        return name
           
    def __save_win(self,winid,time,groupid,group,type,title,filter,pids_data,rollback,scrollback_filename,scrollback_len):
        fname=os.path.join(self.basedir,self.savedir,"win_"+winid)
        if rollback[1]:
            time=linecache.getline(rollback[0],2).strip()
            #copy scrollback
            shutil.move(rollback[1],scrollback_filename)
        basedata=(winid,time,groupid+' '+group,type,title,filter,scrollback_len)
        basedata_len=len(basedata)

        f=open(fname,"w")
        for data in basedata:
            if data:
                f.write(data+'\n')
            else:
                f.write('\n')
        
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
                    #copy vim
                    for file in glob.glob(os.path.join(rollback_dir,line.strip()+'_*')):
                        try:
                            shutil.move(file,os.path.join(self.basedir,self.savedir,os.path.basename(file)))
                        except:
                            out('Unable to rollback: %s'%file)
            os.remove(target)
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
        f.close()
        out("['%s', '%s', '%s', '%s', '%s', '%s' ]"%(basedata[0],basedata[2],basedata[3],basedata[4],basedata[5],basedata[6]))

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
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'scrollback_*')))
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'layout_*')))
                map(os.remove,glob.glob(os.path.join(basedir,savedir,'winlayout_*')))
                linkify(basedir,savedir,self.lastlink)
                return True
            else:
                out('Aborting.')
                return False
        else:
            os.makedirs(os.path.join(basedir,savedir))
            linkify(basedir,savedir,self.lastlink)
            return True

