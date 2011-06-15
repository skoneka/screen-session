#!/usr/bin/env python
# file: kill-group.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill recursively all windows in a group

import sys
import tools

session=sys.argv[1]
groupids=sys.argv[2:]
tools.kill_group(session,tools.require_dumpscreen_window(session,False),groupids)
tools.cleanup()
