#!/usr/bin/env python

import subprocess,sys

print 'Screen Session'
class ScreenSession(object):
    '''class storing GNU screen sessions'''
    pid=""
    basedir=""
    savedir=""

    def __init__(self,pid,basedir,savedir=""):
        self.pid=str(pid)
        self.basedir=str(basedir)
        self.savedir=str(savedir)

    def store(self):
        print 'storing'
        self.__store_screen()

    def load(self):
        print 'loading'

    def __store_screen(self):
        print 'storing screen'
        homewindow=subprocess.Popen('screen -S %s -Q @number' % self.pid, shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        self.__setup_savedir(self.basedir,self.savedir)
        print "Homewindow is " + homewindow
        lastwindow=10
        for i in range(0,lastwindow):
            subprocess.Popen('screen -S %s -X select %d' % (self.pid, i) , shell=True)
            cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
            if(i==int(cwin)):
                print 'current window = '+cwin
                ctty = subprocess.Popen('screen -S %s -Q @tty' % (self.pid) , shell=True, stdout=subprocess.PIPE).communicate()[0]
                print 'current tty = '+ctty

        print "Returning homewindow = " +homewindow
        cwin=subprocess.Popen('screen -S %s -Q @number' % (self.pid), shell=True, stdout=subprocess.PIPE).communicate()[0].split(" ",1)[0]
        print 'current window = '+cwin
#        subprocess.Popen('screen -X select ' + homewindow , shell=True)
    
    def __setup_savedir(self,basedir,savedir):
        print "Setting up session directory %s" % basedir+'/'+savedir

    def __store_proc(self):
        print 'storing proc'

if __name__=='__main__':
    scs=ScreenSession(sys.argv[1],sys.argv[2],sys.argv[1])
    scs.store()

