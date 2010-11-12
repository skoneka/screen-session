#!/usr/bin/env python
import os,sys
import GNUScreen as sc
from util import tmpdir
from ScreenSaver import ScreenSaver


def main():
    logfile="__log-nest-layout"
    dumpfile="__scs-nest-layout-dump-%d"%os.getpid()
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    logfile=os.path.join(tmpdir,logfile)
    dumpfile=os.path.join(tmpdir,dumpfile)
    sys.stdout=open(logfile,'w')
    sys.stderr=sys.stdout
    session=sys.argv[1]
    tlayout=sys.argv[2]

    scs=ScreenSaver(session)
    homelayout,homelayoutname=scs.get_layout_number()
    print ("homelayout: %s"%homelayout)
    focusminsize=scs.focusminsize()
    scs.focusminsize('0 0')
    foff = scs.get_focus_offset()
    hsize=scs.dinfo();
    hsize=int(hsize[0]),int(hsize[1])
    rsize=tuple(map(int,scs.command_at('regionsize').split(' ')))
    rsize=rsize[0],rsize[1]+2 # +1 for caption +1 for hardstatus
    if rsize[0]==hsize[0] and rsize[1]+2==hsize[1]:
        rsize=hsize
    else:
        rsize=rsize[0],rsize[1]+1 # +1 for caption +1 for hardstatus

    scs.layout('select %s'%tlayout)
    print ("tlayout : %s"%scs.get_layout_number()[0])
    tfocusminsize=scs.focusminsize()
    scs.focusminsize('0 0')
    scs.layout('dump %s'%dumpfile)
    tfoff = scs.get_focus_offset()
    winlist=[]
    scs.focus('top')
    region_c = int(os.popen('grep -c "split" %s' % (dumpfile)).readline())+1
    for i in range(0,region_c):
        win=scs.number()
        trsize=scs.command_at('regionsize').split(' ')
        trsizex=int(trsize[0])+1
        trsizey=int(trsize[1])+1
        winlist.append((win,tuple([trsizex,trsizey])))
        scs.focus()
    scs.select_region(tfoff)
    print (winlist)
    scs.focusminsize(tfocusminsize)
    
    print('rsize %s'%str(rsize))
    print('dinfo: %s'%str(hsize))

    scs.layout('select %s'%homelayout)
    scs.source(dumpfile)
    scs.select_region(foff)
    for w in winlist:
        scs.select(w[0])
        x=(w[1][0]*rsize[0])/hsize[0]
        y=(w[1][1]*rsize[1])/hsize[1]
        scs.resize('-h %d'%(x))
        scs.resize('-v %d'%(y))
        print('%s size %d %d'%(w[0], x,y))
        scs.focus()
    scs.select_region(foff+tfoff)
    scs.focusminsize(focusminsize)


if __name__=='__main__':
    main()
