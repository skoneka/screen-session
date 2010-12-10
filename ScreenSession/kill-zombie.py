#!/usr/bin/env python
# file: kill-zombie.py
# author: Artur Skonecki
# website: http://adb.cba.pl
# description: kill all zombie windows in a Screen session

import sys
import tools

session=sys.argv[1]
tools.kill_zombie(session)

