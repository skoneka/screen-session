#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    nest_layout.py : nest a layout in the current region
#
#    Copyright (C) 2010-2011 Artur Skonecki
#
#    Authors: Artur Skonecki http://github.com/skoneka
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import GNUScreen as sc
from util import tmpdir,remove
from ScreenSaver import ScreenSaver


def main():
    logfile = "___log-nest-layout"
    dumpfile = "___scs-nest-layout-dump-%d" % os.getpid()
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    logfile = os.path.join(tmpdir, logfile)
    dumpfile = os.path.join(tmpdir, dumpfile)
    sys.stdout = open(logfile, 'w')
    sys.stderr = sys.stdout
    session = (sys.argv)[1]
    tlayout = (sys.argv)[2]

    scs = ScreenSaver(session)
    (homelayout, homelayoutname) = scs.get_layout_number()

    regions_file_org = regions_file = sc.dumpscreen_layout(scs.pid)
    regions_org = regions = sc.get_regions(regions_file)

    focusminsize = "%s %s" % (regions.focusminsize_x, regions.focusminsize_y)
    regions_c = len(regions.regions)
    foff = regions.focus_offset
    rsize = tuple([int((regions.regions)[foff][1]), int((regions.regions)[foff][2])])
    hsize = (int(regions.term_size_x), int(regions.term_size_y))
    print ("homelayout: %s" % homelayout)
    scs.focusminsize('0 0')
    rsize = (rsize[0], rsize[1] + 2)  # +1 for caption +1 for hardstatus

    scs.layout('select %s' % tlayout, False)
    print ("tlayout : %s" % scs.get_layout_number()[0])
    scs.layout('dump %s' % dumpfile, False)

    regions_file = sc.dumpscreen_layout(scs.pid)
    regions = sc.get_regions(regions_file)

    tfocusminsize = "%s %s" % (regions.focusminsize_x, regions.focusminsize_y)
    regions_c = len(regions.regions)
    tfoff = regions.focus_offset
    hsize = (int(regions.term_size_x), int(regions.term_size_y))

    if rsize[0] == hsize[0] and rsize[1] + 2 == hsize[1]:
        rsize = hsize
    else:
        rsize = (rsize[0], rsize[1] + 1)  # +1 for caption +1 for hardstatus
    rsize = hsize

    print ('rsize %s' % str(rsize))
    print ('dinfo: %s' % str(hsize))

    scs.layout('select %s' % homelayout, False)
    scs.source(dumpfile)

    #sc.load_regions(session, regions_org, None, hsize[0], hsize[1])
    scs.select_region(foff)
    for r in regions.regions:
        if r[0][0] == '-':
            scs.select('-')
        else:
            scs.select(r[0])
        x = ((int(r[1]) + 1) * rsize[0]) / hsize[0]
        y = (int(r[2]) * rsize[1]) / hsize[1]
        scs.resize('-h %d' % x)
        scs.resize('-v %d' % y)
        print ('%s size %d %d' % (r[0], x, y))
        scs.focus()
    scs.select_region(foff + tfoff)
    scs.focusminsize(focusminsize)

    remove(dumpfile)
    remove(regions_file)
    remove(regions_file_org)
    sc.cleanup()

if __name__ == '__main__':
    main()
