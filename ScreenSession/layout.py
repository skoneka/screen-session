#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    find_file.py : find open files in windows
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
import glob
import time
from util import tmpdir, removeit
from ScreenSaver import ScreenSaver
import GNUScreen as sc
from six.moves import map

HISTLEN = 8

layout_dump = 'layout_dump'
layout_regions = 'layout_regions'

class LayoutHistory:
    current = None
    undo = []
    redo = []


def setup_dirs(session, layout):
    global checkpointdir, tdir, tdir_u, tdir_r, tdir_c, tdir_z
    
    session = session.split('.',1)[0]
    checkpointdir = '___layout_checkpoint'

    tdir = os.path.join(tmpdir, '%s/%s/%s' %
            (checkpointdir, session, layout))
    tdir_u = os.path.join(tmpdir, '%s/u' % (tdir))
    tdir_r = os.path.join(tmpdir, '%s/r' % (tdir))
    tdir_c = os.path.join(tmpdir, '%s/L%d_%d' % (tdir, os.getpid(), time.time()))
    tdir_z = os.path.join(tmpdir, '%s/zoom' % (tdir))
    if not os.path.exists(tdir):
        os.makedirs(tdir)

    for d in (tdir_u, tdir_r, tdir_z):
        if not os.path.exists(d):
            os.mkdir(d)


def layout_checkpoint(session, layout):
    ss = ScreenSaver(session)
    layhist = get_layout_history(session, layout)

    os.mkdir(tdir_c)

    tfile1 = os.path.join(tdir_c, layout_dump)
    tfile2 = os.path.join(tdir_c, layout_regions)
    ss.command_at(False , """eval "layout dump '%s'" "dumpscreen layout '%s'" \
            'layout title'""" % (tfile1, tfile2))
    try:
        import filecmp
        for old_current in layhist.current:
            told2 = os.path.join(old_current, os.path.basename(tfile2))
            if filecmp.cmp(told2, tfile2, True):
                told1 = os.path.join(old_current, os.path.basename(tfile1))
                os.remove(told1)
                os.remove(told2)
                os.rmdir(old_current)
            else:
                os.rename(old_current, os.path.join(tdir_u, os.path.basename(old_current)))
    except OSError:
        pass
    
    try:
        for date,redo_dir in layhist.redo:
            os.remove(os.path.join(redo_dir,layout_dump))
            os.remove(os.path.join(redo_dir,layout_regions))
            os.rmdir(redo_dir)
    except OSError:
        pass
    return tfile1,tfile2

def get_layout_history(session, layout):
    layhist = LayoutHistory()

    for f in glob.glob(os.path.join(tdir_u, 'L*')):
        stats = os.stat(f)
        lastmod_date = time.localtime(stats.st_mtime)
        date_file_tuple = (lastmod_date, f)
        layhist.undo.append(date_file_tuple)
    layhist.undo.sort(reverse = True)
    
    n_undo = []
    for (i,e) in enumerate(layhist.undo):
        d,f = e
        if i >= HISTLEN:
            removeit(f)
        else:
            n_undo.append((d,f))
    layhist.undo = n_undo

    for f in glob.glob(os.path.join(tdir_r, 'L*')):
        stats = os.stat(f)
        lastmod_date = time.localtime(stats.st_mtime)
        date_file_tuple = (lastmod_date, f)
        layhist.redo.append(date_file_tuple)
    layhist.redo.sort(reverse = True)

    layhist.current = glob.glob(os.path.join(tdir, 'L*'))
    return layhist



    pass

if __name__ == '__main__':
    mode = (sys.argv)[1]
    session = (sys.argv)[2]
    ss = ScreenSaver(session)
    layout = ss.get_layout_number()[0]
    
    setup_dirs(session, layout)

    if mode in ('undo', 'redo'):
        try:
            targ = int((sys.argv)[3])
        except:
            targ = 1
        if mode == 'undo':
            targ = -targ

        layhist = get_layout_history(session, layout)

        try:
            if targ > 0:
                ld = layhist.redo[targ-1][1]
            elif targ < 0:
                ld = layhist.undo[abs(targ)-1][1]
            else:
                ld = layhist.current[0]
        except IndexError:
            ld = layhist.current[0]
            targ = 0

        cur = layhist.current[0]
        term_x, term_y = list(map(int, ss.dinfo()[0:2]))
        lay_f = sc.layout_begin(session)
        lay_f.write('only\n')
        sc.layout_load_dump(open(os.path.join(ld, layout_dump), 'r'))
        sc.layout_load_regions(sc.get_regions(os.path.join(ld, layout_regions)),
                None, term_x, term_y)
        sc.layout_end()

        os.rename(ld, os.path.join(tdir, os.path.basename(ld)))
        if targ > 0:
            ss.Xecho('layout redo ( %d left )' % (len(layhist.redo) - 1))
            os.rename(cur, os.path.join(tdir_u,
                os.path.basename(cur)))
        elif targ < 0:
            ss.Xecho('layout undo ( %d left )' % (len(layhist.undo) - 1))
            os.rename(cur, os.path.join(tdir_r,
                os.path.basename(cur)))
        else:
            ss.Xecho('layout current ( undo: %d redo: %d )' %
                    (len(layhist.undo), len(layhist.redo)))

    elif mode == 'history':
        layhist = get_layout_history(session, layout)
        try:
            cur = layhist.current[0]
            print ('Path:\n\t%s' % (os.path.split(cur)[0]))
            print ('Current:\n\t%s' % cur.split('/')[-1])
            print ('Undo:')
            for (date, lay) in layhist.undo:
                print('\t' + lay.split('/')[-1])
            print ('Redo:')
            for (date, lay) in layhist.redo:
                print('\t' + lay.split('/')[-1])
        except IndexError:
            print ('No saved snapshots for %s layout %s' % (session, layout))
    elif mode == 'checkpoint':
        layout_checkpoint(session, layout)
    elif mode == 'zoom':
        f_dump, f_regions = layout_checkpoint(session, layout)
        f_z_regions = os.path.join(tdir_z, layout_regions)
        f_z_dump = os.path.join(tdir_z, layout_dump)
        regions_c = sc.get_regions(f_regions)
        if len(regions_c.regions) > 1:
            import shutil
            shutil.copy(f_dump, f_z_dump)
            shutil.copy(f_regions, f_z_regions)
            ss.only()
        elif os.path.exists(f_z_regions):
            regions_z = sc.get_regions(f_z_regions)
            term_x, term_y = list(map(int, ss.dinfo()[0:2]))
            lay_f = sc.layout_begin(session)
            lay_f.write('only\n')
            sc.layout_load_dump(open(f_z_dump, 'r'))

            old_region = regions_z.regions[regions_z.focus_offset]
            current_region = regions_c.regions[regions_c.focus_offset]
            new_region = (current_region[0], old_region[1], old_region[2])
            regions_z.regions[regions_z.focus_offset] = new_region

            sc.layout_load_regions(regions_z, None, term_x, term_y)
            sc.layout_end()
    sc.cleanup()
