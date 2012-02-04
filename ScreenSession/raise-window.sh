#!/bin/sh
# raise a GNU Screen window based on a pattern
# raise.sh [scope] [pattern]
# All windows:
# raise.sh all "CMD vi .*"
# Group specific
# raise.sh .. "CMD vi .*"

SCOPE="$1"
shift 1
O=`screen-session dump $SCOPE |grep -E "^[0-9]* PID [0-9]* $*"`
echo $O
O=`echo $O|cut -d" " -f1`
if [ -z "$O" ]; then
    exit 1
fi
screen -X select $O
exit 0
