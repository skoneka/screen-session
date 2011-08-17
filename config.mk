# screen-session version
VERSION = 0.6.4-devel

# Customize below to fit your system

# paths
INSTFOLDER = /usr/local/share/screen-session

PREFIX = /usr/local

# includes and libs
INCS =
LIBS =

# flags
CPPFLAGS = -DVERSION=\"${VERSION}\" -DCOLOR
CFLAGS = -std=c99 -pedantic -Wall ${INCS} ${CPPFLAGS}
LDFLAGS = -s ${LIBS}
# CFLAGS = -ggdb -std=c99 -pedantic -Wall ${INCS} ${CPPFLAGS}
# LDFLAGS = ${LIBS}

# compiler and linker
CC = cc

# Python binary used in the Makefile
PYTHONBIN = python

