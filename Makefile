# screen-session - GNU Screen session saver

include config.mk

SRC = screen-session-primer.c
OBJ = ${SRC:.c=.o}

all: options screen-session-primer

options:
	@echo screen-session build options:
	@echo "CFLAGS   = ${CFLAGS}"
	@echo "LDFLAGS  = ${LDFLAGS}"
	@echo "CC       = ${CC}"

.c.o:
	@echo CC $<
	@${CC} -c ${CFLAGS} $<

${OBJ}: config.mk

screen-session-primer: ${OBJ}
	@echo CC -o $@
	@${CC} -o $@ ${OBJ} ${LDFLAGS}

clean:
	@echo cleaning
	@rm -f screen-session-primer ${OBJ} screen-session-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	@mkdir -p screen-session-${VERSION}
	@cp -R LICENSE Makefile README config.mk screen-session.diff screen-session screen-session.py ${SRC} screen-session-${VERSION}
	@sed -i "s/^VERSION.*/VERSION='${VERSION}'/" screen-session-${VERSION}/screen-session.py
	@tar -cf screen-session-${VERSION}.tar screen-session-${VERSION}
	@gzip screen-session-${VERSION}.tar
	@rm -rf screen-session-${VERSION}

install: all
	@echo installing executables file to ${DESTDIR}${PREFIX}/bin
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@cp -f screen-session ${DESTDIR}${PREFIX}/bin
	@cp -f screen-session-primer ${DESTDIR}${PREFIX}/bin
	@cp -f screen-session.py ${DESTDIR}${PREFIX}/bin
	@chmod 755 ${DESTDIR}${PREFIX}/bin/screen-session
	@chmod 755 ${DESTDIR}${PREFIX}/bin/screen-session-primer
	@chmod 755 ${DESTDIR}${PREFIX}/bin/screen-session.py

uninstall:
	@echo removing executable file from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session-primer
	@rm -f ${DESTDIR}${PREFIX}/bin/screen-session.py

.PHONY: all options clean dist install uninstall
