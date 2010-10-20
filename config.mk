# screen-session version
VERSION = 0.60

# Customize below to fit your system

# paths
INSTFOLDER = /usr/share/screen-session

PREFIX = /usr

# includes and libs
INCS = 
LIBS = 

# flags
CPPFLAGS = -DVERSION=\"${VERSION}\" -DCOLOR
CFLAGS = -std=c99 -pedantic -Wall -Os ${INCS} ${CPPFLAGS}
LDFLAGS = -s ${LIBS}


# compiler and linker
CC = cc

