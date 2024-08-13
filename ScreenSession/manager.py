#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    manager.py : sessions manager with a split screen preview,
#                 it has few now unecessary hacks (PITA)
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
import re
import sys
import time
import tempfile
import pwd
import mmap
import string
import signal
import GNUScreen as sc
from GNUScreen import SCREEN
import util
from util import tmpdir
from ScreenSaver import ScreenSaver
from help import VERSION
from six.moves import input
try:
    from commands import getoutput
except ImportError:
    from subprocess import getoutput

#try:
#    raw_input
#except NameError:
#    import builtins
#
#    original_input = builtins.input
#    del builtins.input
#
#    def raw_input(*args, **kwargs):
#        return original_input(*args, **kwargs)
#
#    builtins.raw_input = raw_input

tui = 1
tui_focus = 0
maxtui = 3
HOME = os.getenv('HOME')
USER = os.getenv('USER')
HOSTNAME = getoutput('hostname')
configdir = os.path.join(HOME, '.screen-session')


def handler(signum, frame):
    pass

"""
# accountsfile was supposed to hold accounts for the unfinished manager-remote

accountsfile = os.path.join(configdir, 'accounts')

def menu_account(accounts,last_selection):
    try:
        while True:
            #os.system('clear')
            print('Registered accounts "$HOME/.screen-session/accounts":')
            for i,acc in enumerate(accounts):
                if(i==last_selection):
                    sys.stdout.write('->')
                print('\t%d. %s'%(i+1,acc))
            inputstring = input("
Help:\tadd user@host\t del <id>
Choose 1-%d or press Enter: "%(i+1))
            if not inputstring:
                return last_selection
            else:
                try:
                    choice=int(inputstring)
                    if choice==0:
                        return -1
                    elif choice>0 and choice<=i+1:
                        return choice-1
                    else:
                        pass
                except:
                    if inputstring in ('q','Q') :
                        return -1
                    elif inputstring.startswith('h'):
                        print('HELP')
                        input('Press Enter to continue...')
                    elif inputstring.startswith('a'):
                        print('adding')
                        try:
                            account=inputstring.split(' ',1)[1]
                            accounts.append(account)
                            with open(accountsfile,'a') as f:
                                f.write('
'+account.strip())
                        except:
                            input('Usage: add user@host')
                    elif inputstring.startswith('d'):
                        print('deleting')
                        try:
                            i = int(inputstring.split(' ',1)[1])
                            if i > 1:
                                with open(accountsfile,'r') as f:
                                    paccounts = [line.strip() for f in f.readlines()]
                                accounts=[accounts[0]]
                                for a in paccounts:
                                    if a:
                                        accounts.append(a)
                                accounts.pop(i-1)
                                with open(accountsfile,'w') as f:
                                    for a in accounts[1:]:
                                        f.write(a+'
')
                        except:
                            print('Usage: del <id>')
                    else:
                        pass
    except KeyboardInterrupt:
        return -1
"""
menu_tmp_last_selection = -1


def menu_tmp(preselect=None):

    # taken from byobu

    global menu_tmp_last_selection
    choice = ""
    sessions = []
    text = []
    i = 0
    output = getoutput(SCREEN + ' -ls ')
    if output:
        for s in output.split("\n"):
            s = re.sub(r'\s+', " ", s)
            if s.find(" ") == 0 and len(s) > 1:
                text.append(s.strip())
                items = s.split(" ")
                sessions.append(items[1])
                i += 1
    command = None
    inputstring = None
    tries = 0
    while tries < 3:
        sys.stdout.write("""[%s@%s] GNU Screen sessions:
""" % (USER, HOSTNAME))
        i = 1
        for s in text:
            #if sessions[i-1] == menu_tmp_last_selection:
            #    sys.stdout.write(">%d< %s\n" % (i, s))
            #else:
            sys.stdout.write(" %d. %s\n" % (i, s))
            i += 1
        sys.stdout.write(" %d. Create a new session\n" % i)
        i += 1
        try:
            command = None
            inputstring = None
            if preselect:
                inputstring = preselect
            else:
                inputstring = input("\nChoose 1-%d or ?: " % (i - 1))
            if inputstring:
                try:
                    choice = int(inputstring)
                    if choice >= 0 and choice < i:
                        if choice == i-1:
                            command = 'screen'
                        else:
                            menu_tmp_last_selection = sessions[choice - 1]
                        break
                    print2ui('UI: Out of range')
                    os.system('clear')
                except ValueError:  # Specify the exception type
                    command = inputstring
                    break
            else:
                return "enter"
        except KeyboardInterrupt:
            command = "refresh"
            return command
        except EOFError:
            command = "quit"
            return command
        except Exception as e:  # Changed to Python 3 syntax
            if choice == "":
                choice = 1
                break
            tries += 1
            choice = ""
            sys.stderr.write(f"\nERROR: Invalid input: {str(e)}\n")
            None

    if inputstring:
        if command:
            return command
        if choice == 0:

            # Create a new session

            return "quit"
        elif choice == i - 1:
            return "screen"
        else:

            # Attach to the chosen session; must use the 'screen' binary

            return "attach " + sessions[choice - 1]


def prime(fifoname):
    l1 = sc.get_session_list()
    cmd = SCREEN + \
        ' -S "GNU_SCREEN_SESSIONS_MANAGER" -m -d -c /dev/null "%s" "%s" "%s" "%s"' % \
        (os.getenv('PYTHONBIN'), (sys.argv)[0], 'ui', fifoname)
    sys.stderr.write(cmd + "\n")
    os.popen(cmd)
    l2 = sc.get_session_list()
    sys.stderr.write('searching for target session..\n')
    session = sc.find_new_session(l1, l2)
    sys.stderr.write('target session = %s\n' % session)

    print('session: %s' % session)
    return session


def ui2(fifoname):
    sys.stderr.write('starting ui2\n')
    sys.stderr.flush()
    print('ui2 reading [%s]' % fifoname)
    pipein = open(fifoname, 'r')  # open fifo as stdio object
    while 1:
        line = pipein.readline()[:-1]  # blocks until data sent
        print(line)


        #print ('Parent %d got "%s" at %s' % (os.getpid(), line, time.time( )))

ui2pipe = None


def print2pipe(pipeout, line):
    os.write(pipeout, '%s\n' % line)
    pass


def print2ui(line):
    global ui2pipe
    os.write(ui2pipe, '%s\n' % line)
    pass


def reset_tui(scs):
    global tui
    print2ui('TUI = %d' % tui)

    if tui == 0 or tui == 1:
        reset_tui_1(scs)
    elif tui == 2:
        reset_tui_2(scs)
    elif tui == 3:
        reset_tui_3(scs)


def reset_tui_1(scs):
    scs.only()
    scs.split('-v')
    scs.split()
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')
    scs.focus()
    scs.select('1')
    scs.focus('top')

    dinfo = scs.dinfo()
    (term_x, term_y) = (int(dinfo[0]), int(dinfo[1]))
    reg_x = None
    reg_y = None
    if term_x > 100:
        reg_x = 43
    if term_y > 30:
        reg_y = term_y - 15
    if reg_x:
        scs.resize('-h %d' % reg_x)
    if reg_y:
        scs.resize('-v %d' % reg_y)


def reset_tui_3(scs):
    scs.only()
    scs.split()
    scs.split('-v')
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')
    scs.focus()
    scs.select('1')
    scs.focus('top')


def reset_tui_2(scs):
    scs.only()
    scs.split('-v')
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')

    dinfo = scs.dinfo()
    (term_x, term_y) = (int(dinfo[0]), int(dinfo[1]))
    reg_x = None
    if term_x > 100:
        reg_x = 43
    if reg_x:
        scs.resize('-h %d' % reg_x)


def reset_tui_4(scs):
    scs.only()
    scs.split()
    time.sleep(0.1)
    scs.focus('top')
    scs.select('0')


def logic(scs, fifoname, fifoname2, session, psession, last_session):
    sys.stderr.write('starting logic\n')
    sys.stderr.flush()
    ret = None
    global ui2pipe

    #os.system(SCREEN+' -X split -v')

    print('run opening [%s]' % fifoname)
    pipein = open(fifoname, 'r')
    print('run printing')
    sys.stderr.write("%s %s %s\n" % ((sys.argv)[0], 'ui2', fifoname2))
    sys.stdout.flush()
    scs.screen("-t \"diagnostic window\" '%s' '%s' '%s' '%s'" % (os.getenv('PYTHONBIN'),
               (sys.argv)[0], 'ui2', fifoname2))
    pager = os.getenv("PAGER")
    if not pager:
        pager = 'less'
    scs.screen("-t \"help window\" sh -c \"screen-session help manager | %s\"" %
               pager)
    pipeout = os.open(fifoname2, os.O_WRONLY)
    ui2pipe = pipeout
    sys.stdout = os.fdopen(pipeout, 'w')
    reset_tui(scs)
    scs.command_at(False, 'eval "focus bottom" "select 2" "focus top"')

    #scs.focus('bottom')
    #scs.select('2')
    #scs.focus('top')

    if last_session:
        (mode, last_session) = tui_attach_session(scs, last_session,
                psession)

    mode = None
    pid = int(pipein.readline()[:-1].split(' ', 1)[1].strip())
    try:
        while 1:

            line = pipein.readline()[:-1]  # blocks until data sent
            if not line:
                break
                None
            else:
                if line:
                    print2ui('UI: %s' % line)
                ret = None
                e = eval_command(scs, line, last_session, psession,
                                 fifoname2, pid)
                if e:
                    try:
                        if e[1]:
                            if e[1] == '\0':
                                last_session = None
                            else:
                                last_session = e[1]
                            print2ui('LOGIC: select %s' % last_session)
                    except:
                        pass
                    try:
                        if e[0]:
                            mode = e[0]
                    except:
                        pass
                    try:
                        if e[2]:
                            psession = e[2]
                    except:
                        pass
                    
                    if mode and mode != "enter" or (mode == "enter" and \
                        last_session):
                        raise SystemExit
                    else:
                        mode = None
    except SystemExit:
        pipein.close()
        scs.quit()
        return str(tui) + ';' + str(psession) + ';' + str(last_session) + \
            ';;;' + str(mode) + ';' + str(last_session) + ';'


def tui_attach_session(scs, arg, psession):

    #print2ui('LOGIC: attaching \"%s\"'%args[0])

    sys.stderr.write('tui trying to attach %s' % psession)
    scs_target = ScreenSaver(arg)
    if not scs_target.exists():
        print2ui('LOGIC: session does not exists')
        return (None, None)
    scs.focus('bottom')
    cnum = scs.get_number_and_title()[0]
    if scs.sessionname() == arg:
        print2ui('LOGIC: THIS is session [%s]' % arg)
    elif psession and psession == arg:

        print2ui('LOGIC: parent session is [%s]' % psession)
        print2ui('LOGIC: Unable to attach loop detected')
    else:
        scs.screen(SCREEN + ' -x \"%s\"' % arg)
        scs.title(arg)
    if int(cnum) > 2:

        #print2ui('LOGIC: killing window \"%s\"'%cnum)

        scs.kill(cnum)
    scs.focus('top')
    return (None, arg)


def eval_command(scs, command, last_session, psession, fifoname2, ui_pid):
    global menu_tmp_last_selection
    global tui
    command = command.split(" ", 1)
    mode = command[0]
    if len(command) > 1:
        args = []
        for arg in command[1].split(" "):
            args.append(arg)
    else:
        args = [""]

    #print2ui('pid: %d command: %s args: %s'%(ui_pid,command,str(args)))
    #print2ui('trying to send SIGINT to %s'% type(ui_pid))
    #os.kill(ui_pid, signal.SIGINT)
    if mode.startswith('a'):  # attach
        return tui_attach_session(scs, args[0], psession)
    if mode.startswith('d'):  # deselect
        scs.focus('bottom')
        scs.select('-')
        scs.focus('top')
        return (None, '\0')
    elif mode == 'kill' or mode == 'K':
        if last_session:
            menu_tmp_last_selection = -1
            print2ui('LOGIC: killing session \"%s\"' % last_session)
            scst = ScreenSaver(last_session)
            scst.quit()
            scs.focus('top')
    elif mode.startswith('p'):

                               # print

        print2ui((" ").join(["%s" % v for v in args]))
    elif mode.startswith('q'):

                               # quit

        print2ui('LOGIC: quiting...')
        return ("quit", '\0')
    elif mode.startswith('h') or mode == '?':

                                              # help

        scs.focus('bottom')
        cnum = scs.get_number_and_title()[0]
        if int(cnum) > 2:

            #print2ui('LOGIC: killing window \"%s\"'%cnum)

            scs.kill(cnum)

        #scs.command_at(False,'eval "select 2" "focus top"')

        scs.select('2')

        #scs.screen('sh -c "screen-session help manager | less"')

        scs.focus('top')
    elif mode.startswith('e'):

                               # enter

        return ("enter", None)
    elif mode == 'restart':

                          # restart

        print2ui('LOGIC: restarting')
        return ('restart', None)
    elif mode.startswith('f'):

                               # focus top|bottom

        global tui_focus
        if tui_focus == 0:
            scs.focus('bottom')
            tui_focus = 1
            print2ui('LOGIC: focus bottom')
        else:
            scs.focus('top')
            tui_focus = 0
            print2ui('LOGIC: focus top')
    elif mode.startswith('r'):

                               # refresh

        print2ui('LOGIC: refreshing')
    elif mode.startswith('l'):

                               # layout

        print2ui('LOGIC: toggling layout')
        scs.focus('bottom')
        cnum = scs.get_number_and_title()[0]
        scs.focus('top')
        if tui != maxtui:
            tui += 1
        else:
            tui = 1
        reset_tui(scs)
        if int(cnum) > 1:
            scs.focus('bottom')
            scs.select(cnum)
            scs.focus('top')
    elif mode.startswith('L'):

                               # layout

        print2ui('LOGIC: toggling layout')
        scs.focus('bottom')
        cnum = scs.get_number_and_title()[0]
        scs.focus('top')
        if tui != 1:
            tui -= 1
        else:
            tui = maxtui
        reset_tui(scs)
        if int(cnum) > 1:
            scs.focus('bottom')
            scs.select(cnum)
            scs.focus('top')
    elif mode.startswith('w'):

                               # wipe

        print2ui('LOGIC: wiping out dead sessions')
        menu_tmp_last_selection = -1
        scs.wipe()
    elif mode.startswith('save') or mode == 'S':

                                               # save

        if args[0]:
            arg_out = "%s" % args[0]
        else:
            arg_out = "%s" % last_session
        print2ui('LOGIC: saving session as %s' % arg_out)
        os.system('screen-session save -S \"%s\" --force --log \"%s\" \"%s\" 1>&- 2>&-' %
                  (last_session, fifoname2, arg_out))
    elif mode.startswith('s'):

                               # screen

        if args and len(args[0]) > 0:
            arg = (" ").join(["%s" % v for v in args])
        else:
            arg = " "

        cmd = SCREEN + ' -d -m %s' % arg
        print2ui('LOGIC: creating a new session: [%s]' % cmd.strip())
        l1 = sc.get_session_list()
        os.popen(cmd)
        l2 = sc.get_session_list()
        newsession = sc.find_new_session(l1, l2)
        menu_tmp_last_selection = newsession
        print2ui('LOGIC: "%s"' % menu_tmp_last_selection)
        return tui_attach_session(scs, newsession, psession)
    elif mode.startswith('n'):

                               # name

        if last_session:
            print2ui('LOGIC: renaming session to \"%s\"' % args[0])
            if scs.sessionname() == last_session:
                scs_target = scs
            else:
                scs_target = ScreenSaver(last_session, '/dev/null',
                        '/dev/null')

            nsessionname = scs_target.sessionname(args[0])
            print2ui('LOGIC: new sessionname is now [%s]' % nsessionname)
            scs.focus('bottom')
            cnum = scs.get_number_and_title()[0]
            if psession and psession == last_session:
                psession = nsessionname
                print2ui('LOGIC: parent session is now [%s]' %
                         nsessionname)
            elif nsessionname == scs.sessionname():
                print2ui('LOGIC: THIS is session [%s]' % nsessionname)
            else:
                scs.screen(SCREEN + ' -x \"%s\"' % nsessionname)
                scs.title(nsessionname)
            if int(cnum) > 1:

                #print2ui('LOGIC: killing window \"%s\"'%cnum)

                scs.kill(cnum)
            scs.focus('top')
            return (None, nsessionname, psession)
    elif mode == 'pid':
        return ('pid', int(args[0]))
    else:
        print2ui('LOGIC: no such command')


def ui1(fifoname):

    sys.stderr.write('starting ui1\n')
    sys.stderr.flush()
    pipeout = os.open(fifoname, os.O_WRONLY)
    os.write(pipeout, 'pid %d\n' % os.getpid())
    selection = ""
    while selection != None:
        selection = menu_tmp()
        os.system('clear')
        if selection:
            os.write(pipeout, '%s\n' % selection)


    #os.close(pipeout)


def attach_session(session):
    sys.stderr.write('attaching %s' % session)
    os.system(SCREEN + ' -x \"%s\"' % session)


def run(psession):
    signal.signal(signal.SIGINT, handler)
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    #files may get deleted by screen-session need to prevent

    fifoname = os.path.join(tmpdir, '___internal_manager_logic_%s' % os.getpid())
    fifoname2 = os.path.join(tmpdir, '___internal_manager_ui2_%s' % os.getpid())
    last_session = None

    if not os.path.exists(fifoname):
        os.mkfifo(fifoname)
    if not os.path.exists(fifoname2):
        os.mkfifo(fifoname2)
    while True:
        sys.stderr.write('priming..\n')
        session = prime(fifoname)
        session_pid = session.split('.', 1)[0]
        fifoname_access = os.path.join(tmpdir, '__manager_' +
                session_pid)
        os.symlink(fifoname, fifoname_access)
        scs = ScreenSaver(session, '/dev/null', '/dev/null')
        scs.command_at(False, 'setenv SCS_FIFO_ACCESS \"%s\"' %
                       fifoname_access)
        scs.source(os.path.join(os.path.split(os.path.abspath(__file__))[0],
                   'screenrc_MANAGER'))

        #scs.source(os.path.join(HOME,'.screenrc_MANAGER'))

        data = mmap.mmap(-1, 100)

        pid = os.fork()
        if pid == 0:
            command = logic(scs, fifoname, fifoname2, session, psession,
                            last_session)
            try:
                for (i, c) in enumerate(command):
                    data[i] = c
                break
            except:
                pass
        else:
            attach_session(session)
            os.waitpid(pid, 0)
            try:
                os.remove(fifoname_access)
            except:
                pass
            command = data.readline().strip()
            (options, command) = command.split(';;;', 1)
            options = options.split(';')
            command = command.split(';')
            if len(options) > 0:
                tui = int(options[0])
                psession = options[1]
                last_session = options[2]
            if command[0] == "enter":
                print("entering \"%s\"" % command[1])

                #os.execvp('screen',['-x',command[1]])
                #os.system(SCREEN+' -x \"%s\"'%(command[1]))

                attach_session(command[1])
            elif command[0] == 'restart':
                print('restarting...')
                pass
            elif command[0] == 'new':
                cmd = SCREEN + ' -m %s' % command[1]
                print("creating session: [%s]" % cmd)
                os.popen(cmd)
            else:
                try:
                    os.remove(fifoname)
                except:
                    pass
                try:
                    os.remove(fifoname2)
                except:
                    pass
                break
    pass


def main():
    global tui
    sys.stderr.write('starting..\n')
    if sys.argv == 0:
        print('Usage: program [p|ui|ui2] [psession=session or named pipe]')
    if (sys.argv)[1][0] == 'p':
        bMenuRemote = False
        try:
            psession = (sys.argv)[2].split('=', 1)[1]
        except:
            psession = None
        try:
            account = (sys.argv)[3]
        except:
            account = 'current'
            if (sys.argv)[1][1] == 'r':
                bMenuRemote = True
        iaccount = 0
        while True:
            #if bMenuRemote:
            #    f = open(accountsfile, 'r')
            #    accounts_tmp = [line.strip() for line in f.readlines]
            #    accounts = ['%s@%s' % (USER, HOSTNAME)]
            #    for a in accounts_tmp:
            #        if a:
            #            accounts.append(a)
            #    iaccount = menu_account(accounts, iaccount)
            #    if iaccount == -1:
            #        break
            #    elif iaccount == 0:
            #        account = 'current'
            #    else:
            #        account = accounts[iaccount]

            if account != 'current':
                print('Connecting with %s' % account)
                (user, host) = account.split('@', 1)
                if host == 'localhost' or host == HOSTNAME:
                    if user == USER:
                        run(psession)
                    else:
                        os.system('su %s -c "screen-session manager current"' %
                                  user)
                else:
                    os.system('ssh -t %s screen-session manager current' %
                              account)
            else:
                run(psession)
            if not bMenuRemote:
                break
                None
    elif (sys.argv)[1] == 'ui':

        fifoname = (sys.argv)[2]
        ui1(fifoname)
    elif (sys.argv)[1] == 'ui2':
        fifoname = (sys.argv)[2]
        ui2(fifoname)


if __name__ == '__main__':
    log = os.path.join(tmpdir, '___log-manager')
    if not os.path.exists(log):
        sys.stderr = open(log, 'w')
    else:
        sys.stderr = open(log, 'a')
    if not os.path.exists(configdir):
        os.mkdir(configdir)
    #if not os.path.exists(accountsfile):
    #    f = open(accountsfile, 'w')
    #    f.close()
    main()
