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

def out(str,verbosity=0):
    sys.stdout.write(str+'\n')
    sys.stdout.flush()

class ScreenSession(object):
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
    group_other='OTHER_WINDOWS'
    homewindow=""
    
    primer="screen-session-primer"
    
    blacklistfile="BLACKLIST"
    
    blacklist = ["rm","shutdown"]
    
    __wins_trans = {}
    __scrollbacks=[]

    def __init__(self,pid,projectsdir,savedir):
        self.homedir=os.path.expanduser('~')
        self.projectsdir=str(projectsdir)
        self.basedir=os.path.join(self.homedir,self.projectsdir)
        self.savedir=str(savedir)
        self.pid=str(pid)

    def save(self):
        os.system('screen -S %s -X msgminwait %s' % (self.pid,"0"))
        self.homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        out("\n======CREATING___DIRECTORIES======")
        if not self.__setup_savedir(self.basedir,self.savedir):
            return False
        out("\n======SAVING___SCREEN___SESSION======")
        self.__save_screen()
        
        if self.enable_layout:
            out("\n======SAVING___LAYOUTS======")
            self.homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
            self.__save_layouts()
        out("\n======CLEANUP======")
        self.__scrollback_clean()
        return True

    def load(self):
        os.system('screen -S %s -X msgminwait %s' % (self.pid,"0"))
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
        self.homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        if self.exact:
            out('Biggest new window number: %d'%maxnewwindow)
            if self.enable_layout:
                self.__remove_all_layouts()
            out('Moving windows...')
            self.__move_all_windows(maxnewwindow+1,self.group_other,False)
        
        self.homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        out("\n======LOADING___SCREEN___SESSION======")
        self.__load_screen()
        if self.enable_layout:
            out("\n======LOADING___LAYOUTS======")
            self.__load_layouts()
        return True

    def exists(self):
        msg=subprocess.Popen('screen -S %s -Q @echo test' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0]
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
            os.system('screen -S %s -X screen -t \"%s\" %s //group' % (self.pid,rootgroup,0 ) )
            os.system('screen -S %s -X group \"%s\"' % (self.pid,hostgroup) )
        
        rootwindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
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
        os.system('screen -S %s -X select %s' % (self.pid,rootwindow))
        
        # select last selected window
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('screen -S %s -X select %s' % (self.pid,self.__wins_trans[lastid]))
        
        out ("Returning homewindow " +homewindow)
        os.system('screen -S %s -X select %s' % (self.pid,homewindow))
       
        if not self.restore_previous: 
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('screen -S %s -X select %s' % (self.pid,self.__wins_trans[lastid]))



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
            os.system('screen -S %s -X layout remove' % (self.pid) )
            os.system('screen -S %s -X layout next' % (self.pid) )
            currentlayout,currentlayoutname=self.get_layout_number()

    def __kill_windows(self,kill_list):
        #kill_list.pop(len(kill_list)-1)
        for w in kill_list:
            number,title=self.get_number_and_title(w)
            out('killing: '+str(w)+ ':'+number+':'+title)
            os.system('screen -S %s -X at %s kill' % (self.pid, w) )
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
                os.system('screen -S %s -X at %d group %s' % (self.pid,homewindow,'none') )
                
            
            # create wrap group for existing windows
            if not self.bKill:
                os.system('screen -S %s -X screen -t \"%s\" //group' % (self.pid,group) )
                os.system('screen -S %s -X group %s' % (self.pid, 'none') )
                cwin=int(subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])
                group=group+'_'+str(int(time.time()))
                os.system('screen -S %s -X title %s' % (self.pid, group) )
                if cwin not in r:
                    r.append(cwin)
            r.sort()
            r.reverse()
            # move windows by shift and put them in a wrap group
            for i in r:
                cselect = subprocess.Popen('screen -S %s -Q @select %d' % (self.pid,i) , shell=True, stdout=subprocess.PIPE).communicate()[0]
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
                        os.system('screen -S %s -X echo \"%s\"' % (self.pid,msg))
                        searching=True
                else:
                    if(searching):
                        searching=False
                        out('\n--')
                    cwin=int(subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])
                    out('Moving window %d to %d (+%d)'%(cwin,cwin+shift,shift))
                    if cwin==homewindow:
                        homewindow=cwin+shift
                    elif self.bKill:
                        self.__kill_list.append(cwin+shift)
                    
                    cgroup = self.get_group(cwin)
                    if cgroup=="none":
                        os.system('screen -S %s -X group %s' % (self.pid, group) )
                    command='screen -S %s -X number +%d' % (self.pid, shift) 
                    os.system(command)
                    # after moving or kill window number changes so have to update cwin
                    cwin=int(subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0])

            if self.bKill:
                self.__kill_list.reverse()

        os.system('screen -S %s -X select %d' % (self.pid,homewindow))

    def get_lastmsg(self):
        return subprocess.Popen('screen -S %s -Q @lastmsg' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]


    def query_at(self,win,command):
        os.system('screen -S %s -p %s -X %s'% (self.pid,win,command)) 
        l=self.get_lastmsg()
        if l.startswith('Could not'):
            #no such window
            return -1
        else:
            return l
    
    def get_number_and_title(self,win):
        msg=self.query_at(win,'number')
        if msg==-1:
            return -1,-1
        number,title = msg.split("(",1)
        number = number.strip().rsplit(' ',1)[1]
        title = title.rsplit(")",1)[0]
        return number,title

    def get_tty(self,win):
        msg=self.query_at(win,'tty')
        tty = msg.strip()
        return tty

    def get_maxwin(self):
        os.system('screen -S %s -X maxwin ' % (self.pid) )
        msg = self.get_lastmsg()
        maxwin=int(msg.split(':')[1].strip())
        return maxwin
    
    def get_layout_number(self):
        os.system('screen -S %s -X layout number' % (self.pid) )
        msg = self.get_lastmsg()
        if not msg.startswith('This is layout'):
            return -1,-1
        currentlayout,currentlayoutname = msg.split('layout',1)[1].rsplit('(')
        currentlayout = currentlayout.strip()
        currentlayoutname = currentlayoutname.rsplit(')')[0]
        return currentlayout,currentlayoutname
    
    def get_layout_new(self):
        os.system('screen -S %s -X layout new' % (self.pid) )
        msg = self.get_lastmsg()
        if msg.startswith('No more'):
            return False
        else:
            return True

    def get_group(self,win):
        msg=self.query_at(win,'group')
        if msg.endswith('no group'):
            group = 'none'
        else:
            group = msg.rsplit(")",1)[0].split("(",1)[1]
        return group

    def get_exec(self,win):
        msg=self.query_at(win,'exec')
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
        ctime=subprocess.Popen('screen -S %s -Q @time' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
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
                    print('Zombie window. Ignoring.')
                    ctype="zombie"
                    continue;
                elif(ctty=="telnet"):
                    ctype="group"
                    cpids = None
                    cpids_data=None
                elif len(ctty) > 0:
                    ctype="basic"
                    cpids=subprocess.Popen('lsof -F p %s' % (ctty) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split('\n')
                    cpids_data=[]
                    for i,pid in enumerate(cpids):
                        pid=pid[1:]
                        ppid=subprocess.Popen('ps -p %s -o ppid' % (pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split('\n')[1].strip()
                        cppids[pid]=ppid
                        pidinfo=self.__get_pid_info(pid)
                        cpids[i]=pid

                        cpids_data.append(pidinfo)

                
                cgroup = self.get_group(id)
                cfilter = self.get_exec(id)
                
                
                #save scrollback
                scrollback_filename=os.path.join(self.basedir,self.savedir,"scrollback_"+cwin)
                os.system('screen -S %s -X at %s hardcopy -h %s' % (self.pid, cwin, scrollback_filename) )
                self.__scrollbacks.append(scrollback_filename)

                # sort window processes by parent pid
                # what if more than one process has no recognized ppid?
                if cpids:
                    pids_data_sort=[]
                    pids_data_sort_index=0
                    pid_tail=-1
                    pid_tail_c=-1
                    cpids_sort=[]
                    for i,pid in enumerate(cpids):
                        if cppids[pid] not in cppids.keys():
                            pids_data_sort.append(cpids_data[i])
                            cpids_sort.append(pid)
                            pid_tail=pid
                            break;
                    
                    for j in range(len(cpids)):
                        for i,pid in enumerate(cpids):
                            if pid_tail==cppids[pid]:
                                pid_tail=pid
                                pids_data_sort.append(cpids_data[i])
                                cpids_sort.append(pid)
                                break;
                    cpids_data=pids_data_sort
                    cpids=cpids_sort
               

                out('window = '+cwin+\
                        '\ntty = '+ctty  +';  group = '+cgroup+';  type = '+ctype+';  pids = '+str(cpids)+';  title = '+ctitle)
                if cfilter!=-1:
                    out('filter: exec %s'%(cfilter))
                else:
                    cfilter='-1'
                
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

                        out('%s    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (text,pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))
               
                        if(cpids_data[i][2].startswith(self.primer)):
                            out('Instance of primer detected. Importing files.')
                            rollback=self.__rollback(cpids_data[i][2])
                if ctype!="zombie":
                    self.__save_win(cwin,ctime,cgroup,ctype,ctitle,cfilter,cpids_data,rollback)
                rollback=None


        self.linkify(os.path.join(self.basedir,self.savedir),"win_"+homewindow,"last_win")
        out('\n--')
        out('saved on '+ctime)
    
    def __rollback(self,cmdline):
        cmdline=cmdline.split('\0')
        path=os.path.join(self.homedir,cmdline[1],cmdline[3])
        requireme(self.homedir,cmdline[1], cmdline[3],True)
        fhead,ftail=os.path.split(cmdline[3])
        fhhead,fhtail=os.path.split(fhead)
        target=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail+'__rollback')
        try:
            shutil.copy(os.path.join(self.homedir,cmdline[1],cmdline[3]),target)
        except:
            pass
        
        fhead,ftail=os.path.split(cmdline[2])
        fhhead,fhtail=os.path.split(fhead)
        target2=os.path.join(self.homedir,self.projectsdir,self.savedir,ftail)
        try:
            shutil.copy(os.path.join(self.homedir,cmdline[1],cmdline[2]),target2)
        except:
            pass

        if os.path.isfile(target):
            return target
        else:
            return None
        

    def __load_layouts(self):
        homewindow=self.homewindow
        homelayout,homelayoutname=self.get_layout_number()
        if homelayout==-1:
            out("No homelayout")
        layout_trans={}
        for filename in glob.glob(os.path.join(self.basedir,self.savedir,'layout_*')):
            layoutname=filename.split('_',2)[2]
            layoutnumber=filename.split('_',2)[1]
            stat=self.get_layout_new()
            if not stat:
                out('Maximum number of layouts reached. Ignoring layout %s (%s)'%(layoutnumber,layoutname))
            else:
                currentlayout,currentlayoutname=self.get_layout_number()
                
                layout_trans[layoutnumber]=currentlayout

                out("session %s sourcing %s"%(self.pid,filename))
                os.system('screen -S %s -X source \"%s\"' % (self.pid, filename) )
                (head,tail)=os.path.split(filename)
                
                filename2=os.path.join(head,"win"+tail)
                f=open(filename2,'r')
                focus_offset=int(f.readline().split(" ")[1])
                for line in f:
                    line=line.strip()
                    if not line=="-1":
                        try:
                            os.system('screen -S %s -X select %s' % (self.pid,self.__wins_trans[line]))
                        except:
                            out('Unable to set focus for: %s'%line)
                    os.system('screen -S %s -X focus' % (self.pid) )
                f.close()
                
                # restore focus on the right region
                os.system('screen -S %s -X focus top' % (self.pid) )
                for i in range(0,focus_offset):
                    os.system('screen -S %s -X focus' % (self.pid) )
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
            os.system('screen -S %s -X layout select %s' % (self.pid,layout_trans[lastid_l]))
            # ^^ layout numbering may change, use layout_trans={} !

        if homelayout!=-1:
            out("Returning homelayout %s"%homelayout)
            os.system('screen -S %s -X layout select %s' % (self.pid,homelayout))
        else:
            out('No homelayout - unable to return.')
        
        if not self.restore_previous:
            try:
                out("Selecting last layout %s (%s) [ previously %s ]"%(layout_trans[lastid_l],lastname,lastid_l))
                os.system('screen -S %s -X layout select %s' % (self.pid,layout_trans[lastid_l]))
            except:
                pass
        
        # select last selected window
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('screen -S %s -X select %s' % (self.pid,self.__wins_trans[lastid]))
        
        out ("Returning homewindow " +homewindow)
        os.system('screen -S %s -X select %s' % (self.pid,homewindow))
       
        if not self.restore_previous: 
            out("Selecting last window %s [ previously %s ]"%(self.__wins_trans[lastid],lastid))
            os.system('screen -S %s -X select %s' % (self.pid,self.__wins_trans[lastid]))

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
        cnum=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        os.system('screen -S %s -X screen %s -m %d-%d'%(self.pid,self.primer,os.getpid(),self.__get_focus_offset_c))
        #ident="%s -m %d-%d" %(self.primer,os.getpid(),self.__get_focus_offset_c)
        self.__get_focus_offset_c+=1
        markertty = subprocess.Popen('screen -S %s -Q @tty' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
        markernum=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        os.system('screen -S %s -X focus top' % (self.pid) )

        while True:
            ctty = subprocess.Popen('screen -S %s -Q @tty' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
            if ctty==markertty:
                break
            else:
                os.system('screen -S %s -X focus' % (self.pid) )
                focus_offset+=1
        #self.__terminate_processes(ident)
        os.system('screen -S %s -X at %s kill'%(self.pid,markernum))
        os.system('screen -S %s -X select %s' % (self.pid,cnum))
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
        out("Homelayout is %s (%s)"% (homelayout,homelayoutname))
        currentlayout=homelayout
       

        out('--')
        loop_exit_allowed=False
        while currentlayout!=homelayout or not loop_exit_allowed:
            loop_exit_allowed=True
            out("layout = %s (%s)"% (currentlayout,layoutname))
            os.system('screen -S %s -X layout dump \"%s\"' % (self.pid, os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) )
            region_c = int(subprocess.Popen('grep "split" %s | wc -l' % (os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip())+1
            focus_offset=self.__get_focus_offset()
            out("regions (%d); focus offset (%s)" % (region_c,focus_offset))
            os.system('screen -S %s -X focus top' % (self.pid) )
            win=[]
            for i in range(0,region_c):
                currentnumber=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]+'\n'
                windows = subprocess.Popen('screen -S %s -Q @windows' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
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
                    currentnumber="-1\n"
                out("region = %s; window number = %s"%(i,currentnumber.strip()))
                win.append(currentnumber)
                os.system('screen -S %s -X focus' % (self.pid) )

            f=open(os.path.join(self.basedir,self.savedir,"winlayout_"+currentlayout+"_"+layoutname),"w")
            f.writelines("offset %d\n"%focus_offset)
            f.writelines(win)
            f.close()
            
            #get back to originally focused window
            for i in range(0,focus_offset):
                os.system('screen -S %s -X focus' % (self.pid) )


            os.system('screen -S %s -X layout next' % (self.pid) )
            
            currentlayout,layoutname=self.get_layout_number()
            out('--')
        
        self.linkify(os.path.join(self.basedir,self.savedir),"layout_"+homelayout+"_"+homelayoutname,"last_layout")
        
        out("Returned homelayout %s (%s)"% (homelayout,homelayoutname))
        
        # select last selected window
        if os.path.exists(os.path.join(self.basedir,self.savedir,"last_win")):
            last=os.readlink(os.path.join(self.basedir,self.savedir,"last_win"))
            (lasthead,lasttail)=os.path.split(last)
            lastid=lasttail.split("_",1)[1]
            out("Selecting last window %s"%(lastid))
            os.system('screen -S %s -X select %s' % (self.pid,lastid))

        return True
           
    def linkify(self,dir,dest,targ):
        cwd=os.getcwd()
        os.chdir(dir)
        try:
            os.remove(targ)
        except:
            pass
        os.symlink(dest,targ)
        os.chdir(cwd)


    def __save_win(self,winid,time,group,type,title,filter,pids_data,rollback):
        fh=open(os.path.join(self.basedir,self.savedir,"winlist"),'a')
        fh.write(str(winid)+'\n')
        fh.close()
        fname=os.path.join(self.basedir,self.savedir,"win_"+winid)
        
        basedata=(winid,time,group,type,title,filter)

        f=open(fname,"w")
        for data in basedata:
            f.write(data+'\n')
        
        if rollback!=None:
            target=rollback
            fr=open(target,'r')
            for line in fr.readlines()[5:]:
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




    def __get_pid_info(self,pid):
        piddir=os.path.join(self.procdir,pid)
        
        cwd=os.readlink(os.path.join(piddir,"cwd"))
        exe=os.readlink(os.path.join(piddir,"exe"))
        f=open(os.path.join(piddir,"cmdline"),"r")
        cmdline=f.read()
        f.close()
        (exehead,exetail)=os.path.split(exe)
        if exetail in self.blacklist:
            blacklist=True
        else:
            blacklist=False
        
        return (cwd,exe,cmdline,blacklist)

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
                self.linkify(basedir,savedir,self.lastlink)
                f=open(os.path.join(basedir,savedir,'winlist'),'w')
                f.close()
                return True
            else:
                out('Aborting.')
                return False
        else:
            os.makedirs(os.path.join(basedir,savedir))
            self.linkify(basedir,savedir,self.lastlink)
            f=open(os.path.join(basedir,savedir,'winlist'),'w')
            f.close()
            return True


def touch(fname, times = None):
    try:
        os.utime(fname,times)
    except:
        pass

def linkify(dir,dest,targ):
    cwd=os.getcwd()
    os.chdir(dir)
    try:
        os.remove(targ)
    except:
        pass
    os.symlink(dest,targ)
    os.chdir(cwd)

def requireme(home,projectsdir,file_in_session,full=False):
    global archiveend
    global tmpdir
    #os.system("%s -r %s %s"%(primer, os.path.join(home,projectsdir),file_in_session))
    fhead,ftail = os.path.split(file_in_session)
    if os.path.isdir(os.path.join(home,projectsdir,fhead)):
        return
    else:
        unpackme(home,projectsdir,fhead,archiveend,tmpdir,full)

def unpackme(home,projectsdir,savedir,archiveend,tmpdir,full=False):
    out('unpacking...')
    removeit(os.path.join(home,projectsdir,savedir))
    removeit(os.path.join(tmpdir,savedir))
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    if os.path.exists(os.path.join(tmpdir,savedir)):
        shutil.rmtree(os.path.join(tmpdir,savedir))
        os.makedirs(os.path.join(tmpdir,savedir))
    
    cwd=os.getcwd()
    os.chdir(os.path.join(tmpdir))
    if full:
        os.system('tar xjf %s%s'%(os.path.join(home,projectsdir,savedir+'__data'),archiveend))
    os.system('tar xjf %s%s'%(os.path.join(home,projectsdir,savedir+'__win'),archiveend))
    touch(os.path.join(tmpdir,savedir))
    os.chdir(cwd)
    removeit(os.path.join(home,projectsdir,savedir))
    os.symlink(os.path.join(tmpdir,savedir),os.path.join(home,projectsdir,savedir))


def removeit(path):
    try:
        shutil.rmtree(path)
    except:
        try:
            os.remove(path)
        except:
            pass
        pass

def cleantmp(tmpdir,home,projectsdir,archiveend,blacklistfile,lastlink,timeout):
    #cleanup old temporary files and directories
    ctime=time.time()
    files_all=glob.glob(os.path.join(home,projectsdir,'*'))
    files_archives=glob.glob(os.path.join(home,projectsdir,'*%s'%archiveend))
    files_remove=list(set(files_all)-set(files_archives)-set([os.path.join(home,projectsdir,blacklistfile),os.path.join(home,projectsdir,lastlink)]))
    for file in files_remove:
        try:
            delta=ctime-os.path.getmtime(file)
        except:
            delta=timeout+1
        if delta > timeout: # if seconds passed since last modification
            removeit(file)
    files_remove=glob.glob(os.path.join(tmpdir,'*'))
    for file in files_remove:
        try:
            delta=ctime-os.path.getmtime(file)
        except:
            delta=timeout+1
        if delta > timeout: # if seconds passed since last modification
            removeit(file)


def archiveme(tmpdir,home,projectsdir,savedir,archiveend,lastlink,savedir_real):
    cwd=os.getcwd()
    workingpath=tmpdir
    workingpath2=os.path.join(tmpdir,'__tmp_pack')
    if not os.path.exists(workingpath2):
        os.makedirs(workingpath2)
    
    os.chdir(workingpath)
    removeit(os.path.join(workingpath,savedir))
    removeit(os.path.join(workingpath,savedir+'__tmp'))
    removeit(os.path.join(workingpath2,savedir_real))
    removeit(os.path.join(workingpath2,savedir_real+'__tmp'))

    os.remove(os.path.join(home,projectsdir,lastlink))
    shutil.move(os.path.join(home,projectsdir,savedir),os.path.join(workingpath2,savedir_real))
    os.chdir(workingpath2)
    os.mkdir(savedir_real+'__tmp')
    for win in glob.glob(os.path.join(savedir_real,'win_*')):
        os.rename(win,os.path.join(savedir_real+'__tmp',os.path.split(win)[1]))
    os.rename(os.path.join(savedir_real,'last_win'),os.path.join(savedir_real+'__tmp','last_win'))
    
    os.system('tar cjf %s__data%s %s'%(savedir_real,archiveend,savedir_real))
    removeit(os.path.join(workingpath2,savedir_real))
    shutil.move(savedir_real+'__tmp',savedir_real)
    
    os.system('tar cjf %s__win%s %s'%(savedir_real,archiveend,savedir_real))
    removeit(os.path.join(workingpath2,savedir_real))
    
    for file in glob.glob('*'+archiveend):
        removeit(os.path.join(home,projectsdir,file))
        os.rename(file,os.path.join(home,projectsdir,file))

    os.chdir(cwd)
    #os.rename(os.path.join(home,projectsdir,savedir+'__win'+archiveend),os.path.join(home,projectsdir,savedir_real+'__win'+archiveend))
    #os.rename(os.path.join(home,projectsdir,savedir+'__data'+archiveend),os.path.join(home,projectsdir,savedir_real+'__data'+archiveend))
    linkify(os.path.join(home,projectsdir),savedir_real+'__win'+archiveend,lastlink)


def list_sessions(home,projectsdir,archiveend):
    files=glob.glob(os.path.join(home,projectsdir,'*__win'+archiveend))
    
    date_file_list=[]
    for file in files:
        # the tuple element mtime at index 8 is the last-modified-date
        stats = os.stat(file)
        # create tuple (year yyyy, month(1-12), day(1-31), hour(0-23), minute(0-59), second(0-59),
        # weekday(0-6, 0 is monday), Julian day(1-366), daylight flag(-1,0 or 1)) from seconds since epoch
        # note: this tuple can be sorted properly by date and time
        lastmod_date = time.localtime(stats[8])
        date_file_tuple = lastmod_date, file
        date_file_list.append(date_file_tuple)
    
    date_file_list.sort()
    
    if len(date_file_list)>0:
        out('There are saved sessions:')
    else:
        out('There are no saved sessions.')
    
    fileending_l=len(archiveend)+len('__win')
    for file in date_file_list:
        # extract just the filename
        file_name = os.path.split(file[1])[1]
        file_name = file_name[:len(file_name)-fileending_l]
        # convert date tuple to MM/DD/YYYY HH:MM:SS format
        file_date = time.strftime("%m/%d/%y %H:%M:%S", file[0])
        out("\t%-30s %s" % (file_name, file_date))
    
    if len(date_file_list)>0:
        out('%s saved sessions in %s'%(len(date_file_list),os.path.join(home,projectsdir)))



def doexit(var=0,waitfor=True):
    if waitfor:
        raw_input('Press any key to exit...')
    if sys.stdout!=sys.__stdout__:
        sys.stdout.close()
    sys.exit(var)

def usage():
    out('Options:\n\
  --ls\n\
  \tlist saved sessions\n\
    \n\
  -l --load\n\
  \tloading mode\n\
    \n\
  -s --save\n\
  \tsaving mode\n\
    \n\
  -i --in     <session or directory>\n\
  \tinput from session(saving) or savefile(loading)\n\
    \n\
  -o --out    <session or directory>\n\
  \toutput to session(loading) or savefile(saving)\n\
    \n\
  -m --maxwin <number>\n\
  \tsupply biggest window number in your session\n\
    \n\
  -f --force  <number>\n\
  \tforce saving even if savefile with the same\n\
  \talready exists name exists\n\
    \n\
  -x --exact\n\
  \tload session with the same window numbers, move existing windows\n\
  \tto OTHER_WINDOWS group and delete existing layouts\n\
  \n\
  -X --exact-kill-other\n\
  \tsame as exact, but kills all existing windows\n\
  \n\
  -r --restore\n\
  \treturn to home window and home layout after session loading\n\
    \n\
  -y --no-layout\n\
  \tdisable layout saving/loading\n\
    \n\
  --log       <file>\n\
  \toutput to file instead stdout\n\
    \n\
  -d --dir\n\
  \tdirectory holding saved sessions (default: $HOME/.screen-sessions)\n\
    \n\
  -w --wait\n\
  \twait for any key when finished\n\
    \n\
  -h --help\n\
  \tshow this message\n\
  \n\
Examples:\n\
$ screen-session --save --maxwin 20 --in PID --out mysavedsession\n\
$ screen-session --load --in mysavedsession --out PID\n\
\n')

archiveend=''
tmpdir=''

VERSION='git'

class flushfile(object):
  def __init__(self, f):
    self.f = f
  def write(self, x):
    self.f.write(x)
    self.f.flush()

def main():    
    if len(sys.argv)>1:
        if sys.argv[1]=='--wait':
            waitfor=True
        else:
            waitfor=False
    else:
        waitfor = False

    try :
        opts,args = getopt.getopt(sys.argv[1:], "txXryi:c:wfi:o:m:lsd:hv", ["no-nest","exact","exact-kill-other","ls","getopt","unpack=","log=","logpipe=","restore","no-layout","current-session=","wait","force","in=", "out=","maxwin=","load","save","dir=","help"])
    except getopt.GetoptError, err:
        out('Bad options.')
        doexit(2,waitfor)
    
    global archiveend
    global tmpdir
    archiveend='.tar.bz2'
    unpack=None
    current_session=None
    bNest=True
    bExact=False
    bKill=False
    bHelp=False
    bGetopt=False
    bList=False
    restore = False
    verbose = False
    log=None
    logpipe=None
    force = False
    enable_layout = True
    mode = 0
    projectsdir =None
    savedir = None
    maxwin = -1
    input=None
    output=None
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o == "--no-nest":
            bNest=False
        elif o == "--getopt":
            bGetopt=True
        elif o in ("-t","--ls"):
            bList=True
        elif o == "--log":
            log = a
        elif o == "--logpipe":
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
        elif o in ("-w","--wait"):
            waitfor = True
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
            doexit("Unhandled option",waitfor)

    if bGetopt:
        if bList or bHelp or not bNest:
            sys.exit(6)
        else:
            if log:
                print 'log'
                sys.exit(1)
            else:
                print 'nolog'
                sys.exit(0)

    home=os.path.expanduser('~')
    
    if log:
        sys.stdout=open(log,'w')
        sys.stderr=sys.stdout
    elif logpipe:
        sys.stdout=open(logpipe,'w')
        sys.stderr=sys.stdout

        

    out('SCREEN-SESSION ('+VERSION+') - GNU Screen session saver')
    out('written by Artur Skonecki admin<[at]>adb.cba.pl\n')
    
    if bHelp:        
        usage()
        doexit(0,waitfor)
    
    if not projectsdir:
        directory = '.screen-sessions'
        projectsdir = directory
    
    if bList:
        list_sessions(home,projectsdir,archiveend)
        doexit(0,waitfor)
    
    tmpdir=os.path.join(tempfile.gettempdir(),'screen-sessions-'+pwd.getpwuid(os.geteuid())[0] )
    
    if mode==0:
        if unpack:
            unpackme(home,projectsdir,unpack,archiveend,tmpdir,False)
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
    
    
    scs=ScreenSession(pid,projectsdir,savedir)

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

    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    
    ret=0
    if mode==1: #mode save
        savedir_tmp=savedir+'__tmp'
        savedir_real=savedir
        removeit(os.path.join(home,projectsdir,savedir_tmp))
        removeit(os.path.join(tmpdir,savedir_tmp))
        # save and archivize
        if os.path.exists(os.path.join(home,projectsdir,savedir+'__win'+archiveend)):
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
            removeit(os.path.join(tmpdir,savedir_real))
            archiveme(tmpdir,home,projectsdir,savedir,archiveend,scs.lastlink,savedir_real)
            removeit(os.path.join(home,projectsdir,savedir_tmp))
            removeit(os.path.join(tmpdir,savedir_tmp))
            scs.savedir=savedir_real
            savedir=savedir_real
            out('session "%s" saved as "%s" in "%s"'%(scs.pid,scs.savedir,scs.basedir))
            os.system('screen -S %s -X echo "screen-session finished saving"'%scs.pid)
    elif mode==2: #mode load
        #cleanup old temporary files and directories
        cleantmp(tmpdir,home,projectsdir,archiveend,scs.blacklistfile,scs.lastlink,200)
        # unpack and load
        unpackme(home,projectsdir,savedir,archiveend,tmpdir,True)
        try:
            ret = scs.load()
            if scs.bKill:
                scs.kill_old_windows()
        except:
            ret=0
            traceback.out_exc(file=sys.stdout)
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
