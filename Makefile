# screen-session - collection of tools for GNU Screen

include config.mk

DOCS_SRC_0 = README INSTALL NEWS TODO
DOCS_SRC_1 = ${SRCDIR}/help.py
DOCS_GEN = ${SRCDIR}/make_docs.py

SRCDIR = ScreenSession
SRCMAIN1 = ${SRCDIR}/screen-session-primer.c
SRCMAIN2 = ${SRCDIR}/screen-session-helper.c
EXE1 = ${SRCMAIN1:.c=}
EXE2 = ${SRCMAIN2:.c=}
SRCHEAD = ${SRCDIR}/screen-session-define.h
OTHSRC = ${SRCDIR}/screen-session ${SRCDIR}/screen_saver.py ${SRCDIR}/new-window.py ${SRCDIR}/regions.py ${SRCDIR}/screen-session-grab ${SRCDIR}/manager.py  ${SRCDIR}/ScreenSaver.py ${SRCDIR}/__init__.py ${SRCDIR}/GNUScreen.py ${SRCDIR}/util.py ${SRCDIR}/renumber.py ${SRCDIR}/sort.py ${SRCDIR}/kill.py ${SRCDIR}/kill-zombie.py ${SRCDIR}/kill-group.py ${SRCDIR}/sessionname.py ${SRCDIR}/tools.py ${SRCDIR}/dump.py ${SRCDIR}/win-to-group ${SRCDIR}/nest_layout.py ${SRCDIR}/find_pid.py ${SRCDIR}/find_file.py ${SRCDIR}/subwindows.py ${SRCDIR}/screenrc_MANAGER ${SRCDIR}/layoutlist.py ${SRCDIR}/layoutlist_agent.py ${SRCDIR}/layout.py ${DOCS_SRC_1} 


OBJ = ${SRCMAIN1:.c=.o} ${SRCMAIN2:.c=.o}
pwd=`pwd`

all: options ${EXE1} ${EXE2}

options:
	@echo screen-session build options:
	@echo "CFLAGS   = ${CFLAGS}"
	@echo "LDFLAGS  = ${LDFLAGS}"
	@echo "CC       = ${CC}"

${OBJ}: config.mk

${EXE1}: ${SRCMAIN1}  ${SRCHEAD} config.mk
	${CC} -o $@.o -c $@.c ${CFLAGS}
	${CC} -o $@ $@.o ${LDFLAGS}

${EXE2}: ${SRCMAIN2}  ${SRCHEAD} config.mk
	${CC} -o $@.o -c $@.c ${CFLAGS}
	${CC} -o $@ $@.o ${LDFLAGS}

clean:
	@echo cleaning
	@rm -f ${EXE1} ${EXE2} ${OBJ}

clean_www:
	@rm -rf www

docs: www

www: www/index.html

www/index.html: ${DOCS_GEN} ${DOCS_SRC_0} ${DOCS_SRC_1} Makefile
	@echo building html documentation
	@mkdir -p www
	@${PYTHONBIN} ${DOCS_GEN}
	@rm -f ${DOCS_GEN:.py=.pyc} ${DOCS_SRC_1:.py=.pyc}

dist: dist_scs dist_screen
	@cd screen-session-${VERSION}; make docs
	@rm -f screen-session-${VERSION}.tar.gz
	@tar -cf screen-session-${VERSION}.tar screen-session-${VERSION}
	@gzip screen-session-${VERSION}.tar
	@rm -rf screen-session-${VERSION}
	@ls screen-session-${VERSION}.tar.gz

dist_scs:
	@echo creating dist tarball
	@rm -rf screen-session-${VERSION}
	@mkdir -p screen-session-${VERSION} screen-session-${VERSION}/${SRCDIR}
	@cp -R Makefile config.mk configure ${DOCS_SRC_0} screen-session-${VERSION}
	@cp -R ${OTHSRC} ${SRCMAIN2} ${SRCMAIN1} ${SRCHEAD} ${DOCS_GEN} screen-session-${VERSION}/${SRCDIR}
	@sed -i "s/^VERSION.*/VERSION='${VERSION}'/" screen-session-${VERSION}/${SRCDIR}/help.py
	@sed -i "s/VERSION/${VERSION}/" screen-session-${VERSION}/INSTALL

dist_screen:
	@mkdir -p screen-session-${VERSION} screen-session-${VERSION}/screen-4.1.0 \
		screen-session-${VERSION}/screen-4.1.0/doc screen-session-${VERSION}/screen-4.1.0/etc \
		screen-session-${VERSION}/screen-4.1.0/terminfo screen-session-${VERSION}/screen-4.1.0/utf8encodings
	@cp screen-4.1.0/utf8encodings/bf screen-4.1.0/utf8encodings/04 \
	screen-4.1.0/utf8encodings/03 screen-4.1.0/utf8encodings/02 \
	screen-4.1.0/utf8encodings/c6 screen-4.1.0/utf8encodings/cd \
	screen-4.1.0/utf8encodings/18 screen-4.1.0/utf8encodings/c8 \
	screen-4.1.0/utf8encodings/19 screen-4.1.0/utf8encodings/c7 \
	screen-4.1.0/utf8encodings/c4 screen-4.1.0/utf8encodings/c3 \
	screen-4.1.0/utf8encodings/c2 screen-4.1.0/utf8encodings/01 \
	screen-4.1.0/utf8encodings/cc screen-4.1.0/utf8encodings/d6 \
	screen-4.1.0/utf8encodings/a1 \
	screen-session-${VERSION}/screen-4.1.0/utf8encodings
	@cp screen-4.1.0/terminfo/8bits screen-4.1.0/terminfo/screeninfo.src \
	screen-4.1.0/terminfo/screencap screen-4.1.0/terminfo/README \
	screen-4.1.0/terminfo/test.txt screen-4.1.0/terminfo/checktc.c \
	screen-4.1.0/terminfo/tetris.c \
	screen-session-${VERSION}/screen-4.1.0/terminfo
	@cp screen-4.1.0/doc/screen.texinfo screen-4.1.0/doc/Makefile.in \
	screen-4.1.0/doc/screen.info screen-4.1.0/doc/install.sh \
	screen-4.1.0/doc/make.help screen-4.1.0/doc/FAQ \
	screen-4.1.0/doc/README.DOTSCREEN screen-4.1.0/doc/fdpat.ps \
	screen-4.1.0/doc/window_to_display.ps screen-4.1.0/doc/screen.1 \
    screen-session-${VERSION}/screen-4.1.0/doc
	@cp screen-4.1.0/etc/newsyntax screen-4.1.0/etc/mkinstalldirs \
    screen-4.1.0/etc/etcscreenrc screen-4.1.0/etc/us-braille.tbl \
	screen-4.1.0/etc/completer.zsh screen-4.1.0/etc/countmail \
	screen-4.1.0/etc/gr-braille.tbl screen-4.1.0/etc/screenrc \
	screen-4.1.0/etc/ccdefs screen-4.1.0/etc/toolcheck \
	screen-4.1.0/etc/newsyntax38 screen-4.1.0/etc/gs-braille.tbl \
    screen-session-${VERSION}/screen-4.1.0/etc
	@cp screen-4.1.0/screen.c screen-4.1.0/display.h screen-4.1.0/ChangeLog \
	screen-4.1.0/NEWS.3.6 screen-4.1.0/configure.in screen-4.1.0/input.c \
	screen-4.1.0/layer.h screen-4.1.0/mark.h screen-4.1.0/Makefile.in \
	screen-4.1.0/mark.c screen-4.1.0/install.sh screen-4.1.0/misc.c \
	screen-4.1.0/Makefile screen-4.1.0/list_window.c screen-4.1.0/tty.c.dist \
	screen-4.1.0/comm.h.dist screen-4.1.0/NEWS.3.7 screen-4.1.0/window.h \
	screen-4.1.0/viewport.c screen-4.1.0/term.sh screen-4.1.0/sched.h \
	screen-4.1.0/NEWS.3.9 screen-4.1.0/braille.c screen-4.1.0/NEWS \
	screen-4.1.0/encoding.c screen-4.1.0/braille.h screen-4.1.0/README \
	screen-4.1.0/comm.sh screen-4.1.0/kmapdef.c.dist screen-4.1.0/acls.h \
	screen-4.1.0/extern.h screen-4.1.0/term.h.dist \
	screen-4.1.0/sched.c screen-4.1.0/putenv.c screen-4.1.0/window.c \
	screen-4.1.0/viewport.h screen-4.1.0/layout.c \
	screen-4.1.0/INSTALL screen-4.1.0/list_display.c \
	screen-4.1.0/acls.c screen-4.1.0/image.h screen-4.1.0/help.c \
	screen-4.1.0/list_generic.h screen-4.1.0/osdef.sh screen-4.1.0/FAQ \
	screen-4.1.0/utmp.c screen-4.1.0/fileio.c \
	screen-4.1.0/canvas.c screen-4.1.0/process.c screen-4.1.0/ansi.h \
	screen-4.1.0/logfile.c screen-4.1.0/tty.sh screen-4.1.0/termcap.c \
	screen-4.1.0/screen.h screen-4.1.0/configure \
	screen-4.1.0/logfile.h screen-4.1.0/search.c screen-4.1.0/pty.c \
	screen-4.1.0/osdef.h.in screen-4.1.0/socket.c screen-4.1.0/TODO \
	screen-4.1.0/braille_tsi.c screen-4.1.0/COPYING screen-4.1.0/list_generic.c \
	screen-4.1.0/layer.c screen-4.1.0/display.c screen-4.1.0/resize.c \
	screen-4.1.0/patchlevel.h screen-4.1.0/os.h screen-4.1.0/nethack.c \
	screen-4.1.0/NEWS.3.5 screen-4.1.0/loadav.c screen-4.1.0/layout.h \
	screen-4.1.0/config.h.in screen-4.1.0/attacher.c screen-4.1.0/canvas.h \
	screen-4.1.0/ansi.c screen-4.1.0/comm.c screen-4.1.0/term.c \
	screen-4.1.0/teln.c \
    screen-session-${VERSION}/screen-4.1.0

install: all
	@echo installing files to ${DESTDIR}${INSTFOLDER}/
	@mkdir -p ${DESTDIR}${INSTFOLDER}
	@cp -f ${EXE1} ${EXE2} ${OTHSRC} ${DESTDIR}${INSTFOLDER}
	@chmod 755 ${DESTDIR}${INSTFOLDER}/screen-session-helper ${DESTDIR}${INSTFOLDER}/screen-session-primer ${DESTDIR}${INSTFOLDER}/screen-session
	@echo linking executables to ${DESTDIR}${BINDIR}
	@mkdir -p ${DESTDIR}${BINDIR}
	@ln -sf ${DESTDIR}${INSTFOLDER}/screen-session ${DESTDIR}${BINDIR}
	@ln -sf ${DESTDIR}${BINDIR}/screen-session ${DESTDIR}${BINDIR}/scs
	@${PYTHONBIN} -c "import compileall; compileall.compile_dir('${DESTDIR}${INSTFOLDER}',force=1)"
	@echo Remember to install screen-4.1.0

installtest: all
	@echo linking \"${pwd}/${SRCDIR}/screen-session\" to \"${DESTDIR}${BINDIR}/screen-session\"
	@mkdir -p ${DESTDIR}${BINDIR}
	@ln -sf ${pwd}/${SRCDIR}/screen-session ${DESTDIR}${BINDIR}
	@ln -sf ${DESTDIR}${BINDIR}/screen-session ${DESTDIR}${BINDIR}/scs

uninstall:
	@echo removing files from ${DESTDIR}${BINDIR}
	@rm -f ${DESTDIR}${BINDIR}/screen-session
	@rm -f ${DESTDIR}${BINDIR}/scs
	@echo removing directory  ${DESTDIR}${INSTFOLDER}
	@rm -r ${DESTDIR}${INSTFOLDER}

.PHONY: all options clean dist install uninstall docs
