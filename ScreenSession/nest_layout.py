#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    nest_layout.py : nest a layout in the current region
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
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
from util import tmpdir, tmpdir_source, remove
from ScreenSaver import ScreenSaver


def nest_layout(session, src_layuot, dst_layout):
    src_dumpfile = os.path.join(tmpdir_source, 'nest_layout-dump-%d' % os.getpid())

    if not os.path.exists(tmpdir_source):
        os.makedirs(tmpdir_source)

    scs = ScreenSaver(session)

    print('layouts src: %s dst: %s' % (src_layout, dst_layout))

    regions_file_dst = regions_file = sc.dumpscreen_layout(scs.pid)
    regions_dst = sc.get_regions(regions_file)

    dst_focusminsize = "%s %s" % (regions_dst.focusminsize_x, regions_dst.focusminsize_y)
    dst_rsize = (int(regions_dst.regions[regions_dst.focus_offset][1]),
                int(regions_dst.regions[regions_dst.focus_offset][2]))
    dst_term_size = (int(regions_dst.term_size_x),
                    int(regions_dst.term_size_y))
    scs.layout('select %s' % src_layout, False)

    scs.layout('dump %s' % src_dumpfile, False)

    regions_file_src = sc.dumpscreen_layout(scs.pid)
    regions_src = sc.get_regions(regions_file_src)

    src_term_size = (int(regions_src.term_size_x), int(regions_src.term_size_y))

    print ('dst_rsize: %s' % str(dst_rsize))
    print ('src_term_size: %s' % str(src_term_size))

    scs.layout('select %s' % dst_layout, False)
    
    regions_new = sc.Regions()
    regions_new.focus_offset =  regions_dst.focus_offset + regions_src.focus_offset
    regions_new.term_size_x = regions_dst.term_size_x
    regions_new.term_size_y = regions_dst.term_size_y
    regions_new.focusminsize_x = regions_dst.focusminsize_x
    regions_new.focusminsize_y = regions_dst.focusminsize_y
    regions_new.regions = regions_dst.regions[:regions_dst.focus_offset]

    for (window, sizex, sizey) in regions_src.regions:
        print('SRC REGION' + str((window,sizex,sizey)))
        x = (int(sizex) * dst_rsize[0]) / src_term_size[0]
        y = (int(sizey) * dst_rsize[1]) / src_term_size[1]
        print( '%s * %d / %d = %d' % (sizex, dst_rsize[0], src_term_size[0], x))
        print( '%s * %d / %d = %d' % (sizey, dst_rsize[1], src_term_size[0], y))
        regions_new.regions.append((window, str(x), str(y)))

    regions_new.regions = regions_new.regions + regions_dst.regions[regions_dst.focus_offset+1:]
    
    print('destination regions: '+ str(regions_dst.regions))
    print('source regions: ' + str(regions_src.regions))
    print('new regions: ' + str(regions_new.regions))

    sc.layout_begin(session)
    sc.layout_load_dump(open(src_dumpfile, 'r'))
    sc.layout_load_regions(regions_new, None, dst_term_size[0], dst_term_size[1])
    sc.layout_end()

    remove(src_dumpfile)
    remove(regions_file_dst)
    remove(regions_file_src)
    sc.cleanup()

if __name__ == '__main__':
    logfile = os.path.join(tmpdir, '___log_nest-layout')
    sys.stdout = open(logfile, 'w')
    sys.stderr = sys.stdout

    session = (sys.argv)[1]
    src_layout = (sys.argv)[2]

    scs = ScreenSaver(session)
    dst_layout = scs.get_layout_number()[0]

    nest_layout(session, src_layout, dst_layout)
