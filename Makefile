# screen-session - collection of tools for GNU Screen

include config.mk

SRCDIR = ScreenSession
SRC = ${SRCDIR}/screen-session-primer.c
OTHSRC = ${SRCDIR}/screen-session ${SRCDIR}/screen_saver.py ${SRCDIR}/screen-in-dir.py ${SRCDIR}/screen-display-regions.py ${SRCDIR}/screen-display-regions-helper ${SRCDIR}/screen-session-grab ${SRCDIR}/manager.py  ${SRCDIR}/ScreenSaver.py ${SRCDIR}/__init__.py ${SRCDIR}/GNUScreen.py ${SRCDIR}/util.py ${SRCDIR}/renumber.py ${SRCDIR}/sort.py ${SRCDIR}/kill.py ${SRCDIR}/kill-zombie.py ${SRCDIR}/kill-group.py ${SRCDIR}/get_current_session.py ${SRCDIR}/tools.py ${SRCDIR}/help.py

OBJ = ${SRC:.c=.o}
pwd=`pwd`

all: options screen-session-primer

options:
	@echo screen-session build options:
	@echo "CFLAGS   = ${CFLAGS}"
	@echo "LDFLAGS  = ${LDFLAGS}"
	@echo "CC       = ${CC}"

.c.o:
	@echo CC $<
	@${CC} -o $@ -c ${CFLAGS} $<

${OBJ}: config.mk

screen-session-primer: ${OBJ}
	@echo CC -o ${SRCDIR}/$@
	@${CC} -o ${SRCDIR}/$@ ${OBJ} ${LDFLAGS}

clean:
	@echo cleaning
	@rm -f ${SRCDIR}/screen-session-primer ${OBJ} screen-session-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	@mkdir -p screen-session-${VERSION}
	@mkdir -p screen-session-${VERSION}/${SRCDIR}
	@cp -R LICENSE Makefile README INSTALL HOWTO config.mk screen-session.diff  screen-session-${VERSION}
	@cp -R ${OTHSRC} ${SRC} screen-session-${VERSION}/${SRCDIR}
	@sed -i "s/^VERSION.*/VERSION='${VERSION}'/" screen-session-${VERSION}/${SRCDIR}/screen-session.py
	@sed -i "s/^VERSION.*/VERSION='${VERSION}'/" screen-session-${VERSION}/${SRCDIR}/screen-session
	@tar -cf screen-session-${VERSION}.tar screen-session-${VERSION}
	@gzip screen-session-${VERSION}.tar
	@rm -rf screen-session-${VERSION}

install: all
	@echo installing files to ${INSTFOLDER}/
	@mkdir -p ${INSTFOLDER}
	@cp -f ${SRCDIR}/screen-session-primer ${OTHSRC} ${INSTFOLDER}
	@chmod 755 ${INSTFOLDER}/screen-session-primer ${INSTFOLDER}/screen-session
	@echo linking executables to ${DESTDIR}${PREFIX}/bin
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@ln -sf ${INSTFOLDER}/screen-session ${DESTDIR}${PREFIX}/bin
	@ln -sf ${DESTDIR}${PREFIX}/bin/screen-session ${DESTDIR}${PREFIX}/bin/scs
	@ln -sf ${INSTFOLDER}/screen-session-primer ${DESTDIR}${PREFIX}/bin
	@python -c "import compileall; compileall.compile_dir('${INSTFOLDER}',force=1)"

installtest: all
	@echo linking executables in \"${pwd}/${SRCDIR}\" to \"${DESTDIR}${PREFIX}/bin\"
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@ln -sf ${pwd}/${SRCDIR}/screen-session ${DESTDIR}${PREFIX}/bin
	@ln -sf ${DESTDIR}${PREFIX}/bin/screen-session ${DESTDIR}${PREFIX}/bin/scs
	@ln -sf ${pwd}/${SRCDIR}/screen-session-primer ${DESTDIR}${PREFIX}/bin
	
uninstall:
	@echo removing files from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session-primer
	@rm -f ${DESTDIR}${PREFIX}/bin/scs
	@echo removing directory  ${INSTFOLDER}
	@rm -r ${INSTFOLDER}

.PHONY: all options clean dist install uninstall
