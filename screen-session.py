#!/usr/bin/env python

import subprocess,sys,os,getopt,glob


class ScreenSession(object):
    """class storing GNU screen sessions"""
    pid=""
    basedir=""
    savedir=""
    procdir="/proc"
    maxwin=-1
    force=False
    lastdir="last"
    
    #primer arguments: primer_shells primer_whitelist primer_blacklist number_of_processes cwd exe args cwd exe args..
    primer="./screen-session-primer"
    primer_shells = ["zsh","zsh-beta","sh","bash"]
    primer_whitelist = ["vim","man","more","less","most"]
    primer_blacklist = ["screen-session"]
    
    __projectdir=""
    __scrollbacks=[]

    def __init__(self,pid,basedir,savedir):
        self.pid=str(pid)
        self.basedir=str(basedir)
        self.savedir=str(savedir)
        self.__projectdir=os.path.join(self.basedir,self.savedir)

    def save(self):
        print('storing')
        if not self.__setup_savedir(self.basedir,self.savedir):
            return False
        self.__save_screen()
        self.__save_layouts()
        self.__scrollback_clean()

    def load(self):
        print('loading %s' % self.__projectdir)
        self.__load_screen()

    def wizard(self):
        print("running window wizard")
        pass
    
    def __remove_and_escape_bad_chars(self,str):
        return str.replace('|','')#also need to escape "\" with "\\\\"

    def __load_screen(self):
        homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        print ("Homewindow is " +homewindow)
        
        #check if target Screen is currently in some group and set hostgroup to it
        try:
            hostgroup = subprocess.Popen('screen -S %s -Q @group' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" (",1)[1].rsplit(")",1)[0]
        except:
            hostgroup = "none"

        #create root group and put it into host group
        rootgroup="restore_"+self.savedir
        subprocess.Popen('screen -S %s -X screen -t \"%s\" %s //group' % (self.pid,rootgroup,0 ) , shell=True)
        subprocess.Popen('screen -S %s -X group %s' % (self.pid,hostgroup) , shell=True)
        
        rootwindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        print("restoring Screen session inside window %s group %s -> %s" %(rootwindow,hostgroup,rootgroup))

        print('number; time; group; type; title; processes;')
        wins=[]

        for filename in glob.glob(os.path.join(self.__projectdir,'win_*')):
            f=open(filename)
            win=list(f)[0:6]
            f.close()
            win=self.__striplist(win)
            print (str(win))
            wins.append((win[0], win[1], win[2], win[3], self.__remove_and_escape_bad_chars(win[4]), win[5]))


        wins_trans = {}
        for win in wins:
            wins_trans[win[0]]=self.__create_win(False,wins_trans,self.pid,hostgroup,rootgroup,win[0], win[1], win[2], win[3], win[4], win[5])
        
        for win in wins:
            self.__order_group(wins_trans[win[0]],self.pid,hostgroup,rootgroup,win[0], win[1], win[2], win[3], win[4], win[5])
        

        print ("Rootwindow is "+rootwindow)
        print ("Returning homewindow " +homewindow)
        
        subprocess.Popen('screen -S %s -Q @select %s' % (self.pid,homewindow), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]




    # Take a list of string objects and return the same list
    # stripped of extra whitespace.
    def __striplist(self,l):
        return([x.strip() for x in l])


    def __create_win(self,keep_numbering,wins_trans,pid,hostgroup,rootgroup,win,time,group,type,title,processes):
        if type=='basic':
            if keep_numbering:
                subprocess.Popen('screen -S %s -X screen -t \"%s\" %s sh' % (pid,title,win) , shell=True)
            else:
                subprocess.Popen('screen -S %s -X screen -t \"%s\" sh' % (pid,"r_"+title) , shell=True)

        elif type=='group':
            if keep_numbering:
                subprocess.Popen('screen -S %s -X screen -t \"%s\" %s //group' % (pid,title,win ) , shell=True)
            else:
                subprocess.Popen('screen -S %s -X screen -t \"%s\" //group' % (pid,title) , shell=True)
        else:
            print 'Unkown window type. Ignoring.'
            return -1
       

        if keep_numbering:
            newwin = win
        else:
            newwin = subprocess.Popen('screen -S %s -Q @number' % (pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]

        return newwin
    
    def __order_group(self,newwin,pid,hostgroup,rootgroup,win,time,group,type,title,processes):
        if group=="none":
            subprocess.Popen('screen -S %s -X at %s group %s' % (pid,newwin,rootgroup) , shell=True)
        else:    
            subprocess.Popen('screen -S %s -X at %s group %s' % (pid,newwin,group) , shell=True)
            
    def __scrollback_clean(self):
        for f in self.__scrollbacks:
            try:
                #clean up scrollback
                ftmp=f+"_tmp"
                temp=open(ftmp,'w')
                thefile = open(f,'r')
                for line in thefile:
                    if cmp(line,'\n') == 0:
                        line = line.replace('\n','')
                    temp.write(line)
                temp.close()
                thefile.close()
                os.remove(f)
                os.rename(ftmp,f)
            except:
                print 'Unable to clean scrollback file: '+f


    def __save_screen(self):
        homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        print "Homewindow is " + homewindow

        cwin=-1
        ctty=None
        for i in range(0,self.maxwin+1):
            subprocess.Popen('screen -S %s -X select %d' % (self.pid, i) , shell=True)
            print('--')
            ctitle = subprocess.Popen('screen -S %s -Q @title' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
            prev_cwin=cwin
            cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
            if (cwin==prev_cwin):
                print("No such window: window number %d"% i)
            else:
                ctty = subprocess.Popen('screen -S %s -Q @tty' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
                if(ctty=="telnet"):
                    ctype="group"
                    cpids = None
                    cpids_data=None
                else:
                    ctype="basic"
                    cpids=subprocess.Popen('lsof -F p %s' % (ctty) , shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split('\n')
                    cpids_data=[]
                    for i,pid in enumerate(cpids):
                        pid=pid[1:]
                        cpids[i]=pid
                        cpids_data.append(self.__get_pid_info(pid))

                try:
                    cgroup = subprocess.Popen('screen -S %s -Q @group' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" (",1)[1].rsplit(")",1)[0]
                except:
                    cgroup = "none"
                
                ctime=subprocess.Popen('screen -S %s -Q @time' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
                
                #save scrollback
                scrollback_filename=os.path.join(self.basedir,self.savedir,"scrollback_"+cwin)
                subprocess.Popen('screen -S %s -X hardcopy -h %s' % (self.pid, scrollback_filename) , shell=True)
                self.__scrollbacks.append(scrollback_filename)
                
                print('window = '+cwin+ '; saved on '+ctime+\
                        '\ntty = '+ctty  +';  group = '+cgroup+';  type = '+ctype+';  pids = '+str(cpids)+';  title = '+ctitle)
                if(cpids):
                    for i,pid in enumerate(cpids):
                        print('    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))

                self.__save_win(cwin,ctime,cgroup,ctype,ctitle,cpids_data)

                


        print ("Returning homewindow = " +homewindow)
        subprocess.Popen('screen -S %s -Q @select %s' % (self.pid,homewindow), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
#        cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
#        print ('current window = '+cwin)
#        subprocess.Popen('screen -X select ' + homewindow , shell=True)
    

    def __save_layouts(self):
        
        homelayout=subprocess.Popen('screen -S %s -Q @layout number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0]
        if not homelayout.startswith('This is layout'):
            print("No layouts to save")
            return False
        print("Saving layouts")
        homelayout,layoutname = homelayout.split('layout',1)[1].rsplit('(')
        homelayout = homelayout.strip()
        layoutname = layoutname.rsplit(')')[0]
        print("Homelayout is %s (%s)"% (homelayout,layoutname))
        currentlayout=homelayout
       

        loop_exit_allowed=False
        while currentlayout!=homelayout or not loop_exit_allowed:
            loop_exit_allowed=True
            print("currentlayout is %s (%s)"% (currentlayout,layoutname))
            subprocess.Popen('screen -S %s -X layout dump \"%s\"' % (self.pid, os.path.join(self.basedir,self.savedir,"layout_"+currentlayout+"_"+layoutname)) , shell=True)
            subprocess.Popen('screen -S %s -X layout next' % (self.pid) , shell=True)
            
            currentlayout=subprocess.Popen('screen -S %s -Q @layout number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0]
            currentlayout,layoutname = currentlayout.split('layout',1)[1].rsplit('(')
            currentlayout = currentlayout.strip()
            layoutname = layoutname.rsplit(')')[0]
        
        print("Returned homelayout %s (%s)"% (homelayout,layoutname))

        return True
            

    def __save_win(self,winid,time,group,type,title,pids_data):
        fname=os.path.join(self.basedir,self.savedir,"win_"+winid)
        print ("Saving window %s" % winid)
        
        pids_data_len="0"
        if(pids_data):
            pids_data_len=str(len(pids_data))
            
        basedata=(winid,time,group,type,title,pids_data_len)
        f=open(fname,"w")
        for data in basedata:
            f.write(data+'\n')

        if(pids_data):
            for pid in pids_data:
                f.write("-\n")
                for i,data in enumerate(pid):
                    if i == 2:
                        f.write(str(len(data.split('\0'))-1)+'\n')
                        f.write(data+'\n')
                    else:
                        f.write(data+'\n')
        f.close()




    def __get_pid_info(self,pid):
        piddir=os.path.join(self.procdir,pid)
        
        cwd=os.readlink(os.path.join(piddir,"cwd"))
        exe=os.readlink(os.path.join(piddir,"exe"))
        f=open(os.path.join(piddir,"cmdline"),"r")
        cmdline=f.read()
        f.close()
        
        return (cwd,exe,cmdline)

    def __setup_savedir(self,basedir,savefolder):
        savedir = os.path.join(basedir,savefolder)
        print ("Setting up session directory %s" % savedir)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        if os.path.exists(savedir):
            print("Session \"%s\" in \"%s\" already exists. Use --force to overwrite." % (os.path.basename(savedir), basedir))
            if self.force:
                print('forcing..')
                print('cleaning up %s' % savedir)
                for filename in glob.glob(os.path.join(basedir,savedir,'win_*')):
                    os.remove(filename)
                for filename in glob.glob(os.path.join(basedir,savedir,'scrollback_*')):
                    os.remove(filename)
                for filename in glob.glob(os.path.join(basedir,savedir,'layout_*')):
                    os.remove(filename)
                
                cwd=os.getcwd()
                os.chdir(basedir)
                try:
                    os.remove(self.lastdir)
                except:
                    pass
                os.symlink(savedir,self.lastdir)
                os.chdir(cwd)
                
                return True
            else:
                print('Aborting.')
                return False
        else:
            os.makedirs(savedir)
            cwd=os.getcwd()
            os.chdir(basedir)
            try:
                os.remove(self.lastdir)
            except:
                pass
            os.symlink(savedir,self.lastdir)
            os.chdir(cwd)
            return True



def doexit(var=0,waitfor=True):
    if waitfor:
        raw_input('Press any key to exit...')
    sys.exit(var)

def usage():
    print('Usage:')

if __name__=='__main__':
    
    if len(sys.argv)>1:
        if sys.argv[1]=='--wait':
            waitfor=True
        else:
            waitfor=False
    else:
        waitfor = False

    try :
        opts,args = getopt.getopt(sys.argv[1:], "c:wfi:o:m:nwlsd:p:hv", ["current-session=","wait","force","in=", "out=","maxwin=","keep-numbers","wizard","load","save","dir=","pid=","help"])
    except getopt.GetoptError, err:
        print('Bad options.')
        usage()
        doexit(2,waitfor)
    
    current_session=None
    verbose = False
    force = False
    keep_numbers=False
    mode = 0
    basedir =None
    savedir = None
    maxwin = -1
    input=None
    output=None
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-c","--current-session"):
            current_session = a
        elif o in ("-f","--force"):
            force = True
        elif o in ("-n","--keep-numbers"):
            keep_numbers = True
        elif o in ("-h","--help"):
            usage()
            doexit(0,waitfor)
        elif o in ("-w","--wait"):
            waitfor = True
        elif o in ("-m","--maxwin"):
            maxwin = int(a)
        elif o in ("-s","--save"):
            mode = 1
        elif o in ("-l","--load"):
            mode = 2
        elif o in ("-w","--wizard"):
            mode = 3
        elif o in ("-p","--pid"):
            pid = a
        elif o in ("-d","--dir"):
            basedir = a
        elif o in ("-i","--in"):
            input = a
        elif o in ("-o","--out"):
            output = a
        else:
            doexit("Unhandled option",waitfor)


    if not basedir:
        print("basedir not specified, using default:")
        directory = os.path.join(os.path.expanduser('~'),'.screen-sessions')
        print(directory)
        basedir = directory

    if mode==0:
        usage()
        doexit(0,waitfor)
    elif mode==1:
        if not input:
            if current_session:
                input = current_session
            else:
                print("for saving you must specify target Screen session PID as --input")
                doexit("Aborting",waitfor)
        pid = input
        if not output:
            savedir = pid
        else:
            savedir = output
    elif mode == 2:
        if not input:
            print("for loading you must specify saved Screen session as --input")
            doexit("Aborting",waitfor)
        if not output:
            if current_session:
                output = current_session
            else:
                print("for loading you must specify target Screen session PID as --output")
                doexit("Aborting",waitfor)
        pid = output
        savedir = input
    
    if (maxwin==-1) and (mode==1):
        print("for saving specify --maxwin (biggest window number in session)")
        doexit("Aborting",waitfor)
    
    scs=ScreenSession(pid,basedir,savedir)
    if savedir == scs.lastdir:
        print("savedir cannot be named \"%s\". Aborting." % savedir)
        doexit(1,waitfor)

    scs.maxwin = maxwin
    scs.force = force
    if mode==1:
        scs.save()
    elif mode==2:
        scs.load()
    elif mode==3:
        scs.wizard()
    else:
        print('No mode specified --load or --save')

    doexit(0,waitfor)


