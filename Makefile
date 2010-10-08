# screen-session - GNU Screen session saver

include config.mk

SRCDIR = ScreenSession
SRC = ${SRCDIR}/screen-session-primer.c
OTHSRC = ${SRCDIR}/screen-session ${SRCDIR}/screen-session.py ${SRCDIR}/screen-in-dir ${SRCDIR}/screen-display-regions.py ${SRCDIR}/screen-display-regions-helper ${SRCDIR}/screen-session-grab ${SRCDIR}/screen-session-manage  ${SRCDIR}/ScreenSaver.py ${SRCDIR}/__init__.py ${SRCDIR}/GNUScreen.py ${SRCDIR}/util.py
OBJ = ${SRC:.c=.o}

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
	@cp -R LICENSE Makefile README config.mk screen-session.diff  screen-session-${VERSION}
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
	@ln -sf ${INSTFOLDER}/screen-session-primer ${DESTDIR}${PREFIX}/bin

uninstall:
	@echo removing files from ${INSTFOLDER}
	@rm -f ${INSTFOLDER}/screen-session
	@rm -f ${INSTFOLDER}/screen-session-primer
	@echo removing directory  ${INSTFOLDER}
	@rm -r ${INSTFOLDER}
	@echo removing files from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session-primer

.PHONY: all options clean dist install uninstall
