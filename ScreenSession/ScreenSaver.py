
import subprocess,sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,linecache

from util import out,requireme,linkify,which
import GNUScreen as sc

class ScreenSaver(object):
    """class storing GNU screen sessions"""
    pid="" # actually it is sessionname
    basedir=""
    projectsdir=".screen-sessions"
    savedir=""
    procdir="/proc"
    maxwin=-1
    force=False
    lastlink="last"
    enable_layout = False
    restore_previous = False
    exact=False
    bKill=False
    bVim=True
    group_other='OTHER_WINDOWS'
    homewindow=""
    screen=None
    
    primer="screen-session-primer"
    
    # blacklist file in projects directory
    blacklistfile="BLACKLIST"
    
    # old static blacklist
    blacklist = ("rm","shutdown")
   
    vim_names = ('vi','vim')
    __wins_trans = {}
    __scrollbacks=[]

    def __init__(self,pid,projectsdir='/dev/null',savedir='/dev/null'):
        self.screen='%s -S %s'%(which('screen')[0],pid)
        self.homedir=os.path.expanduser('~')
        self.projectsdir=str(projectsdir)
        self.basedir=os.path.join(self.homedir,self.projectsdir)
        self.savedir=str(savedir)
        self.pid=str(pid)

    def save(self):
        os.system('%s -X msgminwait %s' % (self.screen,"0"))
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
        os.system('%s -X msgminwait %s' % (self.screen,"0"))
        out('session "%s" loading "%s"' % (self.pid,os.path.join(self.basedir,self.savedir)))
        #check if the saved session exists and get the biggest saved window number and a number of saved windows
        maxnewwindow=0
        newwindows=0
        try:
            f = open(os.path.join(self.basedir,self.savedir,"winlist"),'r')
            winlist=f.readlines()
            newwindows=len(winlist)
            maxnewwindow=int(winlist[newwindows-1])
            f.close()
            out('%d new windows'%newwindows)
        except:
            out('Unable to open.')
            return False
        

        # keep original numbering, move existing windows
        self.homewindow=subprocess.Popen('%s -Q @number' % (self.screen), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        if self.exact:
            out('Biggest new window number: %d'%maxnewwindow)
            if self.enable_layout:
                self.__remove_all_layouts()
            out('Moving windows...')
            self.__move_all_windows(maxnewwindow+1,self.group_other,False)
        
        self.homewindow=subprocess.Popen('%s -Q @number' % (self.screen), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        out("\n======LOADING___SCREEN___SESSION======")
        self.__load_screen()
        if self.enable_layout:
            out("\n======LOADING___LAYOUTS======")
            self.__load_layouts()
        return True

    def exists(self):
        msg=subprocess.Popen('%s -Q @echo test' % (self.screen), shell=True, stdout=subprocess.PIPE).communicate()[0]
        if msg.startswith('No screen session found'):
            return False
        else:
            return True

    def __remove_and_escape_bad_chars(self,str):
        # some characters are causing problems when setting window titles
        return str.replace('\\','\\\\\\\\').replace('|','I')# how to properly escape "|"?

    def __load_screen(self):
        homewindow=self.homewindow
        out ("Homewindow is " +homewindow)
        
        #check if target Screen is currently in some group and set hostgroup to it
        hostgroup = self.get_group(homewindow)

        #create root group and put it into host group
        if self.exact:
            rootgroup='none'
            hostgroup='none'
        else:
            rootgroup="restore_"+self.savedir
            os.system('%s -X screen -t \"%s\" %s //group' % (self.screen,rootgroup,0 ) )
            os.system('%s -X group \"%s\"' % (self.screen,hostgroup) )
        
        rootwindow=subprocess.Popen('%s -Q @number' % (self.screen), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        out("restoring Screen session inside window %s (%s)" %(rootwindow,rootgroup))

        out('number; time; group; type; title; filter; processes;')
        wins=[]
        f = open(os.path.join(self.basedir,self.savedir,"winlist"),'r')
        for id in f:
            try:
                filename=os.path.join(self.basedir,self.savedir,"win_"+id.strip())
                f=open(filename)
                win=list(f)[0:7]
                f.close()
                win=self.__striplist(win)
                out (str(win))
                wins.append((win[0], win[1], win[2], win[3], self.__remove_and_escape_bad_chars(win[4]), win[5], win[6]))
            except:
                out('Unable to load window %s'%id)
        f.close()


        for win in wins:
            self.__wins_trans[win[0]]=self.__create_win(self.exact,self.__wins_trans,self.pid,hostgroup,rootgroup,win[0], win[1], win[2], win[3], win[4], win[5],win[6])
        
        for win in wins:
            self.__order_group(self.__wins_trans[win[0]],self.pid,hostgroup,rootgroup,win[0], win[1], win[2], win[3], win[4], win[5], win[6])
        
        out ("Rootwindow is "+rootwindow)
        os.system('%s -X select %s' % (self.screen,rootwindow))
        
        # select last selected window
        lastid=''
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            self.select(self.__wins_trans[lastid])
        
        out ("Returning homewindow " +homewindow)
        self.select(homewindow)
       
        if not self.restore_previous: 
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            self.select(self.__wins_trans[lastid])



    # Take a list of string objects and return the same list
    # stripped of extra whitespace.
    def __striplist(self,l):
        return([x.strip() for x in l])


    def __create_win(self,keep_numbering,wins_trans,pid,hostgroup,rootgroup,win,time,group,type,title,filter,processes):
        if keep_numbering:
            winarg=win
        else:
            winarg=""
        
        if type=='basic':
            os.system('screen -S %s -X screen -t \"%s\" %s %s %s %s %s' % (pid,title,winarg,self.primer,self.projectsdir,os.path.join(self.savedir,"scrollback_"+win),os.path.join(self.savedir,"win_"+win)) )
        elif type=='group':
            os.system('screen -S %s -X screen -t \"%s\" %s //group' % (pid,title,winarg ) )
        else:
            out ('Unkown window type. Ignoring.')
            return -1
       
        newwin = subprocess.Popen('screen -S %s -Q @number' % (pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        return newwin
    
    def __order_group(self,newwin,pid,hostgroup,rootgroup,win,time,group,type,title,filter,processes):
        if group=="none":
            os.system('screen -S %s -X at %s group %s' % (pid,newwin,rootgroup) )
        else:    
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
            os.system('%s -X layout remove' % (self.screen) )
            os.system('%s -X layout next' % (self.screen) )
            currentlayout,currentlayoutname=self.get_layout_number()

    def __kill_windows(self,kill_list):
        #kill_list.pop(len(kill_list)-1)
        for w in kill_list:
            number,title=self.get_number_and_title(w)
            out('killing: '+str(w)+ ':'+number+':'+title)
            os.system('%s -X at %s kill' % (self.screen, w) )
    def kill_old_windows(self):
        out ('killing: '+str(self.__kill_list))
        self.__kill_windows(self.__kill_list)

    def __move_all_windows(self,shift,group,kill=False):
        homewindow=int(self.homewindow)
        cwin=-1
        ctty=None
        cppids={}
        searching=False

        if self.maxwin>0:
            r=range(0,self.maxwin+1)
            
            if self.bKill:
                self.__kill_list=[]
                #self.__kill_list.append(homewindow+shift)
                os.system('%s -X at %d group %s' % (self.screen,homewindow,'none') )
                
            
            # create wrap group for existing windows
            if not self.bKill:
                os.system('%s -X screen -t \"%s\" //group' % (self.screen,group) )
                os.system('%s -X group %s' % (self.screen, 'none') )
                cwin=int(subprocess.Popen('%s -Q @number' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])
                group=group+'_'+str(int(time.time()))
                os.system('%s -X title %s' % (self.screen, group) )
                if cwin not in r:
                    r.append(cwin)
            r.sort()
            r.reverse()
            # move windows by shift and put them in a wrap group
            for i in r:
                cselect = subprocess.Popen('%s -Q @select %d' % (self.screen,i) , shell=True, stdout=subprocess.PIPE).communicate()[0]
                if not searching:
                    out('--')
                if len(cselect)>0 and not cselect.startswith('This'):
                    #no such window
                    if searching:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    else:
                        msg='Searching for windows (set --maxwin)...'
                        sys.stdout.write('\n'+msg)
                        os.system('%s -X echo \"%s\"' % (self.screen,msg))
                        searching=True
                else:
                    if(searching):
                        searching=False
                        out('\n--')
                    cwin=int(subprocess.Popen('%s -Q @number' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])
                    out('Moving window %d to %d (+%d)'%(cwin,cwin+shift,shift))
                    if cwin==homewindow:
                        homewindow=cwin+shift
                    elif self.bKill:
                        self.__kill_list.append(cwin+shift)
                    
                    cgroup = self.get_group(cwin)
                    if cgroup=="none":
                        os.system('%s -X group %s' % (self.screen, group) )
                    command='%s -X number +%d' % (self.screen, shift) 
                    os.system(command)
                    # after moving or kill window number changes so have to update cwin
                    cwin=int(subprocess.Popen('%s -Q @number' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])

            if self.bKill:
                self.__kill_list.reverse()

        os.system('%s -X select %d' % (self.screen,homewindow))

    def get_lastmsg(self):
        return subprocess.Popen('%s -Q @lastmsg' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0]


    def command_at(self,command,win="-1"):
        if win=="-1":
            win=""
        else:
            win="-p %s"%win
        os.system('%s %s -X %s'% (self.screen,win,command)) 
        l=self.get_lastmsg()
        if l.startswith('Could not'):
            #no such window
            return -1
        else:
            return l
    
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

    def get_tty(self,win="-1"):
        msg=self.command_at('tty',win)
        tty = msg.strip()
        return tty

    def get_maxwin(self):
        msg=self.command_at('maxwin')
        maxwin=int(msg.split(':')[1].strip())
        return maxwin
    '''
    def get_info(self,win):
       
        msg=self.command_at('info',win)
        return msg
    '''
    def get_info(self,win="-1"):
        msg=self.command_at('info',win)
        if not msg.endswith('no window'):
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
    
    def get_dinfo(self):
        msg=self.command_at('dinfo')
        msg = msg.split(' ')
        nmsg=msg.pop(0).strip('(').rstrip(')').split(',',1)
        nmsg=nmsg+msg
        return nmsg

    def number(self,args='',win="-1"):
        msg=self.command_at('number %s'%args,win)
        return msg
    
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

    def split(self,args=''):
        msg=self.command_at('split %s'%args)

    def screen(self,args='',win="-1"):
        msg=self.command_at('screen %s'%args,win)
        return msg

    def source(self,args=''):
        msg=self.command_at('source %s'%args)
        return msg

    def select(self,args='',win="-1"):
        msg=self.command_at('select %s'%args,win)
        return msg
    def wipe(self,args=''):
        os.popen('screen -wipe %s'%args)

    def backtick(self,id,lifespan='',autorefresh='',args=''):
        msg=self.command_at('backtick %s %s %s %s'%(id,lifespan,autorefresh,args))

    def focusminsize(self,args=''):
        msg=self.command_at('focusminsize %s'%args)

    def get_layout_number(self):
        msg=self.command_at('layout number')
        if not msg.startswith('This is layout'):
            return -1,-1
        currentlayout,currentlayoutname = msg.split('layout',1)[1].rsplit('(')
        currentlayout = currentlayout.strip()
        currentlayoutname = currentlayoutname.rsplit(')')[0]
        return currentlayout,currentlayoutname
    
    def get_layout_new(self):
        msg=self.command_at('layout new')
        if msg.startswith('No more'):
            return False
        else:
            return True
    def get_group(self,win="-1"):
        msg=self.command_at('group',win)
        if msg.endswith('no group'):
            group = 'none'
        else:
            group = msg.rsplit(")",1)[0].split("(",1)[1]
        return group

    def get_exec(self,win):
        msg=self.command_at('exec',win)
        msg = msg.split(':',1)[1].strip()
        if msg.startswith('(none)'):
            return -1
        else:
            return msg


    def __save_screen(self):
        homewindow=self.homewindow
        out ("Homewindow is " + homewindow)

        cwin=-1
        ctty=None
        cppids={}
        searching=False
        rollback=None
        ctime=subprocess.Popen('%s -Q @time' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0]
        for i in range(0,self.maxwin+1):
            id=str(i)
            if not searching:
                out('--')
            cwin,ctitle=self.get_number_and_title(id)
            if (cwin==-1):
                #no such window
                if searching:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                else: 
                    sys.stdout.write('\nSearching for windows (set --maxwin)...')
                    searching=True
            else:
                if(searching):
                    searching=False
                    out('\n--')

                # has to follow get_number_and_title() to recognize zombie windows
                ctty = self.get_tty(id) 
                if ctty.startswith('This'):
                    out('%s is a zombie window. Ignoring.'%(cwin))
                    ctype="zombie"
                    continue;

                cfilter = self.get_exec(id)
                cgroup = self.get_group(id)
                
                
                # display some output
                out(cwin+'; tty = '+ctty  +';  group = '+cgroup+';  title = '+ctitle)
                if cfilter!=-1:
                    out('filter: exec %s'%(cfilter))
                else:
                    cfilter='-1'

                if(ctty=="telnet"):
                    ctype="group"
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
                            out('%s: Unable to access. SUID?'%pid)
                    cpids=ncpids
                
                out('type = '+ctype +'; pids = '+str(cpids))

                if(cpids):
                    for i,pid in enumerate(cpids):
                        if(cpids_data[i][3]):
                            text="BLACKLISTED"
                        else: 
                            text=""
                        if self.primer in cpids_data[i][2]:
                            # clean zsh -c 'primer..' by removing '-c' 'primer..'
                            l=cpids_data[i][2].split('\0')
                            if l[1]=='-c' and l[2].startswith(self.primer):
                                s=str(l[0])+'\0'
                                for j in range(3,len(l)):
                                    s+=str(l[j])+'\0'
                                    out('appending: %s'%str(l[j]))
                                newdata=(cpids_data[i][0],cpids_data[i][1],s,cpids_data[i][3])
                                cpids_data[i]=newdata

                        #out('%s    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (text,pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))
                        vim_name=str(None)
                        arg0=cpids_data[i][2].split('\0')[0]
                        if self.primer==arg0:
                            out('Instance of primer detected. Importing files.')
                            rollback=self.__rollback(cpids_data[i][2])
                        elif arg0 in self.vim_names and self.bVim:
                            vim_name=self.__save_vim(cwin)
                        
                        cpids_data[i]=(cpids_data[i][0],cpids_data[i][1],cpids_data[i][2],cpids_data[i][3],vim_name)
                if not rollback:
                    # save scrollback
                    scrollback_filename=os.path.join(self.basedir,self.savedir,"scrollback_"+cwin)
                    os.system('%s -X at %s hardcopy -h %s' % (self.screen, cwin, scrollback_filename) )
                    self.__scrollbacks.append(scrollback_filename)

                if ctype!="zombie":
                    self.__save_win(cwin,ctime,cgroup,ctype,ctitle,cfilter,cpids_data,rollback,scrollback_filename)
                rollback=None


        linkify(os.path.join(self.basedir,self.savedir),"win_"+homewindow,"last_win")
        out('\n--')
        out('saved on '+ctime)
    
    def __rollback(self,cmdline):
        try:
            cmdline=cmdline.split('\0')
            requireme(self.homedir,cmdline[1], cmdline[2],True)
            path=os.path.join(self.homedir,cmdline[1],cmdline[3])
            fhead,ftail=os.path.split(cmdline[3])
            fhhead,fhtail=os.path.split(fhead)
            target=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            
            number=ftail.split('_')[1]
            oldsavedir=fhead
            
            try:
                shutil.move(os.path.join(self.homedir,cmdline[1],cmdline[3]),target)
            except Exception,e:
                out(str(e))
                pass
            
            fhead,ftail=os.path.split(cmdline[2])
            fhhead,fhtail=os.path.split(fhead)
            target2=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
            try:
                shutil.move(os.path.join(self.homedir,cmdline[1],cmdline[2]),target2)
            except Exception,e:
                out(str(e))
                pass

            source3=os.path.join(self.homedir,cmdline[1],oldsavedir,"vim_"+number)
            target3=None
            if os.path.isfile(source3):
                target3=os.path.join(self.homedir,self.projectsdir,self.savedir,"vim_"+number+'__rollback')
                try:
                    shutil.move(source3,target3)
                except:
                    pass

            if os.path.isfile(target):
                return target,target2,target3
            else:
                return None
        except:
            return None
        

    def __load_layouts(self):
        cdinfo=map(int,self.get_dinfo()[0:2])
        out('Terminal size: %s %s'%(cdinfo[0],cdinfo[1]))
        homewindow=self.homewindow
        homelayout,homelayoutname=self.get_layout_number()
        if homelayout==-1:
            out("No homelayout")
        layout_trans={}
        out('--')
        layout_c=len(glob.glob(os.path.join(self.basedir,self.savedir,'layout_*')))
        for i in range(0,layout_c):
            filename=glob.glob(os.path.join(self.basedir,self.savedir,'layout_%d_*'%i))[0]
            layoutname=filename.split('_',2)[2]
            layoutnumber=filename.split('_',2)[1]
            stat=self.get_layout_new()
            if not stat:
                out('Maximum number of layouts reached. Ignoring layout %s (%s)'%(layoutnumber,layoutname))
            else:
                currentlayout,currentlayoutname=self.get_layout_number()
                
                layout_trans[layoutnumber]=currentlayout

                out("sourcing %s"%(filename))
                os.system('%s -X source \"%s\"' % (self.screen, filename) )
                (head,tail)=os.path.split(filename)
                
                filename2=os.path.join(head,"win"+tail) #read winlayout
                f=open(filename2,'r')
                focus_offset=int(f.readline().split(" ")[1])
                dinfo=map(int,f.readline().split(" ")[1:])
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
                            os.system('%s -X select %s' % (self.screen,self.__wins_trans[window]))
                        except:
                            out('Unable to set focus for: %s'%window)
                    os.system('%s -X focus' % (self.screen) )
                f.close()
                

                # set region dimensions
                os.system('%s -X focus top' % (self.screen) )
                for size in regions_size:
                    if size[0]>0:
                        out('region size: %d %d'%(size[0],size[1]))
                        self.resize('-h %d'%(size[0]))
                        self.resize('-v %d'%(size[1]))
                        self.fit()
                    os.system('%s -X focus' % (self.screen) )

                
                # restore focus on the right region
                os.system('%s -X focus top' % (self.screen) )
                for i in range(0,focus_offset):
                    os.system('%s -X focus' % (self.screen) )

                out('--')



        # select last layout
        lastname=None
        lastid_l=None
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_layout")) and len(layout_trans)>0:
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_layout"))
            (lasthead,lasttail)=os.path.split(last)
            last=lasttail.split("_",2)
            lastname=last[2]
            lastid_l=last[1]
            out("Selecting last layout %s (%s) [ previously %s ]"%(layout_trans[lastid_l],lastname,lastid_l))
            os.system('%s -X layout select %s' % (self.screen,layout_trans[lastid_l]))
            # ^^ layout numbering may change, use layout_trans={} !

        if homelayout!=-1:
            out("Returning homelayout %s"%homelayout)
            os.system('%s -X layout select %s' % (self.screen,homelayout))
        else:
            out('No homelayout - unable to return.')
        
        if not self.restore_previous:
            try:
                out("Selecting last layout %s (%s) [ previously %s ]"%(layout_trans[lastid_l],lastname,lastid_l))
                os.system('%s -X layout select %s' % (self.screen,layout_trans[lastid_l]))
            except:
                pass
        
        # select last selected window
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('%s -X select %s' % (self.screen,self.__wins_trans[lastid]))
        
        out ("Returning homewindow " +homewindow)
        os.system('%s -X select %s' % (self.screen,homewindow))
       
        if not self.restore_previous: 
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('%s -X select %s' % (self.screen,self.__wins_trans[lastid]))

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
    def __get_focus_offset(self):
        focus_offset=0
        cnum=subprocess.Popen('%s -Q @number' % self.screen, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        os.system('%s -X screen %s -m %d-%d'%(self.screen,self.primer,os.getpid(),self.__get_focus_offset_c))
        #ident="%s -m %d-%d" %(self.primer,os.getpid(),self.__get_focus_offset_c)
        self.__get_focus_offset_c+=1
        markertty = self.get_tty()
        markernum,markertitle=self.get_number_and_title()
        #out('markernum=%s; title=%s;'%(markernum,markertitle))
        os.system('%s -X focus top' % (self.screen) )


        while True:
            ctty = subprocess.Popen('%s -Q @tty' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0]
            if ctty==markertty:
                break
            else:
                os.system('%s -X focus' % (self.screen) )
                focus_offset+=1
        #self.__terminate_processes(ident)
        os.system('%s -p %s -X kill'%(self.screen,markernum))
        os.system('%s -X select %s' % (self.screen,cnum))
        return focus_offset

    def parse_windows(self,windows):
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

    def __save_layouts(self):
        homelayout,homelayoutname=self.get_layout_number()
        layoutname=homelayoutname
        
        if homelayout==-1:
            out("No layouts to save. Create layouts with \":layout new\"")
            return False
        dinfo=self.get_dinfo()
        out('Terminal size: %s %s'%(dinfo[0],dinfo[1]))
        out("Homelayout is %s (%s)"% (homelayout,homelayoutname))
        currentlayout=homelayout
       

        out('--')
        loop_exit_allowed=False
        while currentlayout!=homelayout or not loop_exit_allowed:
            loop_exit_allowed=True
            out("%s (%s)"% (currentlayout,layoutname))
            os.system('%s -X layout dump \"%s\"' % (self.screen, os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) )
            region_c = int(subprocess.Popen('grep "split" %s | wc -l' % (os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip())+1
            focus_offset=self.__get_focus_offset()
            out("regions (%d); focus offset (%s)" % (region_c,focus_offset))
            os.system('%s -X focus top' % (self.screen) )
            win=[]
            for i in range(0,region_c):
                currentnumber=subprocess.Popen('%s -Q @number' % self.screen, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
                windows = subprocess.Popen('%s -Q @windows' % (self.screen) , shell=True, stdout=subprocess.PIPE).communicate()[0]
                csize=self.get_regionsize(currentnumber)
                offset=0
                findactive=False
                wnums,wactive=self.parse_windows(windows)
                #out 'cnum='+currentnumber.strip()+'; wactive='+str(wactive)
                #out windows
                if wactive==-1:
                    findactive=False
                else:
                    findactive=True

                if not findactive:
                    currentnumber="-1"
                sizex=int(csize[0])
                sizey=int(csize[1])
                win.append("%s %d %d\n"%(currentnumber,sizex+1,sizey+1))
                out("region = %s; window number = %s; size = (%d,%d)"%(i,currentnumber,sizex,sizey))
                os.system('%s -X focus' % (self.screen) )

            f=open(os.path.join(self.basedir,self.savedir,"winlayout_"+currentlayout+"_"+layoutname),"w")
            f.writelines("offset %d\n"%focus_offset)
            f.writelines("dinfo %s %s\n"%(dinfo[0],dinfo[1]))
            f.writelines(win)
            f.close()
            
            #get back to originally focused window
            for i in range(0,focus_offset):
                os.system('%s -X focus' % (self.screen) )


            os.system('%s -X layout next' % (self.screen) )
            
            currentlayout,layoutname=self.get_layout_number()
            out('--')
        
        linkify(os.path.join(self.basedir,self.savedir),"layout_"+homelayout+"_"+homelayoutname,"last_layout")
        
        out("Returned homelayout %s (%s)"% (homelayout,homelayoutname))
        
        os.system('%s -X select %s' % (self.screen,self.homewindow_last))

        return True

    def __save_vim(self,winid):
        name="vim_%s"%(winid)
        fname=os.path.join(self.basedir,self.savedir,name)
        self.stuff('^[^[:mksession %s^M'%fname, winid)
        return name
           
    def __save_win(self,winid,time,group,type,title,filter,pids_data,rollback,scrollback_filename):
        fh=open(os.path.join(self.basedir,self.savedir,"winlist"),'a')
        fh.write(str(winid)+'\n')
        fh.close()
        fname=os.path.join(self.basedir,self.savedir,"win_"+winid)
        if rollback:
            time=linecache.getline(rollback[0],2).strip()
            #copy scrollback
            shutil.move(rollback[1],scrollback_filename)
            try:
                vim_fname=os.path.join(self.basedir,self.savedir,"vim_"+winid)
                shutil.move(rollback[2],vim_fname)
            except:
                pass
        basedata=(winid,time,group,type,title,filter)

        f=open(fname,"w")
        for data in basedata:
            f.write(data+'\n')
        
        if rollback:
            target=rollback[0]
            fr=open(target,'r')
            for line in fr.readlines()[6:]:
                f.write(line)
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
                f=open(os.path.join(basedir,savedir,'winlist'),'w')
                f.close()
                return True
            else:
                out('Aborting.')
                return False
        else:
            os.makedirs(os.path.join(basedir,savedir))
            linkify(basedir,savedir,self.lastlink)
            f=open(os.path.join(basedir,savedir,'winlist'),'w')
            f.close()
            return True

