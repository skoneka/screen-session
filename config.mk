# screen-session version
VERSION = 0.6.6cyanogilvie

# Customize below to fit your system

# paths
# use DESTDIR as in http://www.gnu.org/prep/standards/standards.html#DESTDIR
# e.g. make DESTDIR=/tmp/install install
BINDIR = /usr/local/bin
INSTFOLDER = /usr/local/share/screen-session

# includes and libs
INCS =
LIBS =

# flags
CPPFLAGS = -DVERSION=\"${VERSION}\" -DCOLOR
CFLAGS = -std=c99 -pedantic -Wall ${INCS} ${CPPFLAGS}
LDFLAGS = -s ${LIBS}

# compiler and linker
CC = cc

# Python binary used in the Makefile
PYTHONBIN = python

