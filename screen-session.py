#!/usr/bin/env python

import subprocess,sys,os


print 'Screen Session'
class ScreenSession(object):
    """class storing GNU screen sessions"""
    pid=""
    basedir=""
    savedir=""
    procdir="/proc"

    def __init__(self,pid,basedir,savedir):
        self.pid=str(pid)
        self.basedir=str(basedir)
        self.savedir=str(savedir)

    def store(self):
        print('storing')
        self.__store_screen()

    def load(self):
        print 'loading'

    def __store_screen(self):
        print 'storing screen'
        homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        if not self.__setup_savedir(self.basedir,self.savedir):
            return False
        print "Homewindow is " + homewindow

        lastwindow=10
        for i in range(0,lastwindow):
            subprocess.Popen('screen -S %s -X select %d' % (self.pid, i) , shell=True)
            cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
            if(i==int(cwin)):
                print('--')
                ctitle = subprocess.Popen('screen -S %s -Q @title' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
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
                
                subprocess.Popen('screen -S %s -X hardcopy -h %s' % (self.pid, os.path.join(self.basedir,self.savedir,cwin+"_scrollback")) , shell=True)
                
                print('window = '+cwin+ '; saved on '+ctime+\
                        '\ntty = '+ctty  +';  group = '+cgroup+';  type = '+ctype+';  pids = '+str(cpids)+';  title = '+ctitle)
                if(cpids):
                    for i,pid in enumerate(cpids):
                        print('    pid = %s:     cwd = %s;  exe = %s;  cmdline = %s' % (pid, cpids_data[i][0], cpids_data[i][1], cpids_data[i][2]))
                #self.__setup_windir(self.basedir,self.savedir,cwin)

                self.__save_win(cwin,ctime,cgroup,ctype,ctitle,cpids_data)

                


        print ("Returning homewindow = " +homewindow)
        subprocess.Popen('screen -S %s -Q @select %s' % (self.pid,homewindow), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        print ('current window = '+cwin)
#        subprocess.Popen('screen -X select ' + homewindow , shell=True)
    

    def __save_win(self,winid,time,group,type,title,pids_data):
        fname=os.path.join(self.basedir,self.savedir,winid)
        print ("Saving window %s" % winid)
        
        pids_data_len="0"
        if(pids_data):
            pids_data_len=str(len(pids_data))
            
        basedata=(time,group,type,title,pids_data_len)
        f=open(fname,"w")
        for data in basedata:
            f.write(data+'\n')

        if(pids_data):
            for pid in pids_data:
                f.write("-\n")
                for data in pid:
                    f.write(data+'\n')
        f.close()




    def __get_pid_info(self,pid):
        piddir=os.path.join(self.procdir,pid)
        
        cwd=os.readlink(os.path.join(piddir,"cwd"))
        exe=os.readlink(os.path.join(piddir,"exe"))
        f=open(os.path.join(piddir,"cmdline"),"r")
        cmdline=f.read()
        f.close()
        
        (exehead,exetail)=os.path.split(exe)
        cmdline=cmdline[len(exetail):]
        return (cwd,exetail,cmdline)


    def __setup_windir(self,basedir,savedir,winid):
        windir=os.path.join(basedir,savedir,winid)
        print ("Setting up window directory %s" % windir)
        os.makedirs(windir)

    def __setup_savedir(self,basedir,savefolder):
        savedir = os.path.join(basedir,savefolder)
        print ("Setting up session directory %s" % savedir)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        if os.path.exists(savedir):
            print("Session \"%s\" in \"%s\" already exists. Aborting" % (savedir, basedir))
            return False
        else:
            os.makedirs(savedir)
            return True

    def __submit_window(self,tty,win):
        pass

    def __store_proc(self):
        print 'storing proc'

if __name__=='__main__':
    # pid basedir
    scs=ScreenSession(sys.argv[1],sys.argv[2],sys.argv[1])
    scs.store()

