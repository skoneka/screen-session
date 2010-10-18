#!/usr/bin/env python

import os,sys
import GNUScreen as sc

def get_sessionname():
    p=os.popen('screen -X sessionname')
    p.close()
    p=os.popen('screen -Q @lastmsg')
    s=p.read()
    return s.split('\'',1)[1].rsplit('\'',1)[0]

try:
    s=get_sessionname()
except:
    s=None
    sclist=sc.get_session_list()
    badname=os.getenv('STY').split('.',1)[0]
    for sc,active in sclist:
        if sc.startswith(badname):
            s=sc
if s:
    try:
        newname=sys.argv[1]
        os.system('screen -S %s -X sessionname %s'%(s,newname))
    except:
        print(s)
        sys.exit(0)
else:
    print '__no__session__'
    sys.exit(1)

