# screen-session version
VERSION = 0.52

# Customize below to fit your system

# paths
PREFIX = /usr/local

# includes and libs
INCS = 
LIBS = 

# flags
CPPFLAGS = -DVERSION=\"${VERSION}\" -DCOLOR
CFLAGS = -ggdb -std=c99 -pedantic -Wall -Os ${INCS} ${CPPFLAGS}
LDFLAGS = -s ${LIBS}


# compiler and linker
CC = cc

