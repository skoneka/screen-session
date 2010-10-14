#!/usr/bin/env python

import os
p=os.popen('screen -X sessionname')
p.close()
p=os.popen('screen -Q @lastmsg')
s=p.read()
try:
    s=s.split('\'',1)[1].rsplit('\'',1)[0]
except:
    s='__no__session__'
print s

