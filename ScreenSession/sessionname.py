#!/usr/bin/env python

import os,sys
import GNUScreen as sc
from util import timeout_command
from GNUScreen import SCREEN

# sessions must have a display (must be attached) to be detected

def get_sessionname(session=None):
    if session:
        session_arg='-S '+session
    else:
        session_arg=''
    p=os.popen(SCREEN+' %s -X sessionname'%session_arg).close()
    s=timeout_command(SCREEN+' %s -Q @lastmsg'%session_arg,3)[0]
    return s.split('\'',1)[1].rsplit('\'',1)[0]

try:
    if sys.argv[1]!="__no__session__":
        session=sys.argv[1]
    else:
        raise Exception
except:
    session=None
try:
    s=get_sessionname(session)
except:
    s=None
    s2=None
    try:
        badname=os.getenv('STY').split('.',1)[0]
        if not badname:
            session=None
            raise Exception
        sclist=sc.get_session_list()
        for sc,active in sclist:
            if sc.startswith(badname):
                s=sc
                if not sc.endswith('-queryA'):
                    break;
    except:
        pass
if s:
    try:
        if session and s.find(session)>-1:
            newname=sys.argv[2]
            os.popen(SCREEN+' -S %s -X sessionname %s'%(s,newname)).close()
        else:
            raise Exception
    except:
        if not session or s.find(session)>-1:
            print(s)
            sys.exit(0)
        else:
            print ('__no__session__')
            sys.exit(1)
else:
    print ('__no__session__')
    sys.exit(1)

