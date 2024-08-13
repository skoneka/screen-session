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
OTHSRC = ${SRCDIR}/screen-session \
         ${SRCDIR}/screen_saver.py \
         ${SRCDIR}/new-window.py \
         ${SRCDIR}/regions.py \
         ${SRCDIR}/screen-session-grab \
         ${SRCDIR}/manager.py \
         ${SRCDIR}/ScreenSaver.py \
         ${SRCDIR}/__init__.py \
         ${SRCDIR}/GNUScreen.py \
         ${SRCDIR}/util.py \
         ${SRCDIR}/renumber.py \
         ${SRCDIR}/sort.py \
         ${SRCDIR}/kill.py \
         ${SRCDIR}/kill-zombie.py ${SRCDIR}/kill-group.py \
         ${SRCDIR}/sessionname.py \
         ${SRCDIR}/tools.py \
         ${SRCDIR}/dump.py \
         ${SRCDIR}/win-to-group \
         ${SRCDIR}/nest_layout.py \
         ${SRCDIR}/find_pid.py \
         ${SRCDIR}/find_file.py \
         ${SRCDIR}/subwindows.py \
         ${SRCDIR}/screenrc_MANAGER \
         ${SRCDIR}/layoutlist.py ${SRCDIR}/layoutlist_agent.py \
         ${SRCDIR}/layout.py \
         ${SRCDIR}/raise-window.sh \
         ${SRCDIR}/run-or-raise-and-quit.sh \
         ${SRCDIR}/run-or-raise.sh \
         ${SRCDIR}/send-escape.sh \
         ${DOCS_SRC_1}


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
	( cd escreen/src; ./autogen.sh && ./configure )
	@mkdir -p \
		screen-session-${VERSION}/escreen/src/doc screen-session-${VERSION}/escreen/src/etc \
		screen-session-${VERSION}/escreen/src/terminfo screen-session-${VERSION}/escreen/src/utf8encodings
	@cp escreen/src/utf8encodings/* screen-session-${VERSION}/escreen/src/utf8encodings/
	@cp escreen/src/terminfo/* screen-session-${VERSION}/escreen/src/terminfo/
	@cp -a escreen/src/doc/* screen-session-${VERSION}/escreen/src/doc/
	@cp escreen/src/etc/* screen-session-${VERSION}/escreen/src/etc/
	@cp escreen/src/*.c escreen/src/*.h escreen/src/*.sh escreen/src/*.in escreen/src/ChangeLog \
		escreen/src/NEWS* escreen/src/README escreen/src/HACKING escreen/src/INSTALL escreen/src/TODO \
		escreen/src/FAQ escreen/src/COPYING escreen/src/Makefile escreen/src/configure \
		screen-session-${VERSION}/escreen/src/

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
	@echo Remember to install escreen

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
