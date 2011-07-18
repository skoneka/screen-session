#!/usr/bin/env python
import os,sys
import GNUScreen as sc
from util import tmpdir
from ScreenSaver import ScreenSaver


def main():
    logfile="___log-nest-layout"
    dumpfile="___scs-nest-layout-dump-%d"%os.getpid()
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
    while True:
        regions=sc.get_regions(scs.pid)
        try:
            focusminsize="%s %s"%(regions.focusminsize_x, regions.focusminsize_y)
            regions_c=regions.number_of_regions
            foff=regions.focus_offset
            rsize=tuple([int(regions.regions[foff][1]),int(regions.regions[foff][2])])
            hsize=int(regions.term_size_x),int(regions.term_size_y)
            if regions.regions:
                break
        except Exception:
            sys.exit(2)
            pass
    print ("homelayout: %s"%homelayout)
    scs.focusminsize('0 0')
    rsize=rsize[0],rsize[1]+2 # +1 for caption +1 for hardstatus

    scs.layout('select %s'%tlayout,False)
    print ("tlayout : %s"%scs.get_layout_number()[0])
    scs.layout('dump %s'%dumpfile,False)
    while True:
        regions=sc.get_regions(scs.pid)
        try:
            tfocusminsize="%s %s"%(regions.focusminsize_x, regions.focusminsize_y)
            regions_c=regions.number_of_regions
            tfoff=regions.focus_offset
            hsize=int(regions.term_size_x),int(regions.term_size_y)
            if regions.regions:
                break
        except:
            pass

    if rsize[0]==hsize[0] and rsize[1]+2==hsize[1]:
        rsize=hsize
    else:
        rsize=rsize[0],rsize[1]+1 # +1 for caption +1 for hardstatus
    rsize=hsize
    
    print('rsize %s'%str(rsize))
    print('dinfo: %s'%str(hsize))

    scs.layout('select %s'%homelayout,False)
    scs.source(dumpfile)
    scs.select_region(foff)
    for r in regions.regions:
        if r[0][0]=='-':
            scs.select('-')
        else:
            scs.select(r[0])
        x=((int(r[1])+1)*rsize[0])/hsize[0]
        y=(int(r[2])*rsize[1])/hsize[1]
        scs.resize('-h %d'%(x))
        scs.resize('-v %d'%(y))
        print('%s size %d %d'%(r[0], x,y))
        scs.focus()
    scs.select_region(foff+tfoff)
    scs.focusminsize(focusminsize)
    os.remove(dumpfile)

if __name__=='__main__':
    main()
