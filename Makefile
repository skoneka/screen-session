# screen-session - collection of tools for GNU Screen

include config.mk

SRCDIR = ScreenSession
#SRC = ${SRCDIR}/screen-session-primer.c 
SRCMAIN1 = ${SRCDIR}/screen-session-primer.c 
SRCMAIN2 = ${SRCDIR}/screen-session-helper.c 
SRCHEAD = ${SRCDIR}/screen-session-define.h 
OTHSRC = ${SRCDIR}/screen-session ${SRCDIR}/screen_saver.py ${SRCDIR}/new-window.py ${SRCDIR}/regions.py ${SRCDIR}/screen-session-grab ${SRCDIR}/manager.py  ${SRCDIR}/ScreenSaver.py ${SRCDIR}/__init__.py ${SRCDIR}/GNUScreen.py ${SRCDIR}/util.py ${SRCDIR}/renumber.py ${SRCDIR}/sort.py ${SRCDIR}/kill.py ${SRCDIR}/kill-zombie.py ${SRCDIR}/kill-group.py ${SRCDIR}/sessionname.py ${SRCDIR}/tools.py ${SRCDIR}/help.py ${SRCDIR}/dump.py ${SRCDIR}/win-to-group ${SRCDIR}/nest_layout.py ${SRCDIR}/find_pid.py ${SRCDIR}/find_file.py

OBJ = ${SRC:.c=.o}
pwd=`pwd`

all: screen-session-primer screen-session-helper

options:
	@echo screen-session build options:
	@echo "CFLAGS   = ${CFLAGS}"
	@echo "LDFLAGS  = ${LDFLAGS}"
	@echo "CC       = ${CC}"

#.c.o:
#	${CC} -o $@ -c ${CFLAGS} $<

${OBJ}: config.mk

#screen-session-primer: ${OBJ}
#	${CC} -o ${SRCDIR}/$@ ${OBJ} ${LDFLAGS}

screen-session-primer: ${SRCMAIN1}  ${SRCHEAD} config.mk
	${CC} -o ${SRCDIR}/$@ ${SRCDIR}/$@.c ${LDFLAGS} ${CFLAGS}

screen-session-helper: ${SRCMAIN2}  ${SRCHEAD} config.mk
	${CC} -o ${SRCDIR}/$@ ${SRCDIR}/$@.c ${LDFLAGS} ${CFLAGS}

clean:
	@echo cleaning
	@rm -f ${SRCDIR}/screen-session-helper ${SRCDIR}/screen-session-primer ${OBJ}

dist:
	@echo creating dist tarball
	@mkdir -p screen-session-${VERSION}
	@mkdir -p screen-session-${VERSION}/${SRCDIR}
	@cp -R Makefile config.mk LICENSE README INSTALL HOWTO TODO gnu_screen.diff  screen-session-${VERSION}
	@cp -R ${OTHSRC} ${SRCMAIN2} ${SRCMAIN1} screen-session-${VERSION}/${SRCDIR}
	@sed -i "s/^VERSION.*/VERSION='${VERSION}'/" screen-session-${VERSION}/${SRCDIR}/help.py
	@rm -f screen-session-${VERSION}.tar.gz
	@tar -cf screen-session-${VERSION}.tar screen-session-${VERSION}
	@gzip screen-session-${VERSION}.tar
	@rm -rf screen-session-${VERSION}

install: all
	@echo installing files to ${INSTFOLDER}/
	@mkdir -p ${INSTFOLDER}
	@cp -f ${SRCDIR}/screen-session-primer ${OTHSRC} ${INSTFOLDER}
	@cp -f ${SRCDIR}/screen-session-helper ${OTHSRC} ${INSTFOLDER}
	@chmod 755 ${INSTFOLDER}/screen-session-helper ${INSTFOLDER}/screen-session-primer ${INSTFOLDER}/screen-session
	@echo linking executables to ${DESTDIR}${PREFIX}/bin
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@ln -sf ${INSTFOLDER}/screen-session ${DESTDIR}${PREFIX}/bin
	@ln -sf ${DESTDIR}${PREFIX}/bin/screen-session ${DESTDIR}${PREFIX}/bin/scs
	@python -c "import compileall; compileall.compile_dir('${INSTFOLDER}',force=1)"

installtest: all
	@echo linking executables in \"${pwd}/${SRCDIR}\" to \"${DESTDIR}${PREFIX}/bin\"
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@ln -sf ${pwd}/${SRCDIR}/screen-session ${DESTDIR}${PREFIX}/bin
	@ln -sf ${DESTDIR}${PREFIX}/bin/screen-session ${DESTDIR}${PREFIX}/bin/scs
	
uninstall:
	@echo removing files from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session
	@rm -f ${DESTDIR}${PREFIX}/bin/scs
	@echo removing directory  ${INSTFOLDER}
	@rm -r ${INSTFOLDER}

.PHONY: all options clean dist install uninstall
