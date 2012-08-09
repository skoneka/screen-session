#!/bin/sh
# raise a GNU Screen window based on a pattern
# raise.sh [scope] [pattern]
# All windows:
# raise-window.sh "CMD vi .*" all
# Group specific
# raise-window.sh "CMD vi .*" ..
SCRIPTPATH=$(dirname $(realpath $0)); cd $SCRIPTPATH || exit 1;

[ "$SCOPE" ] || SCOPE="all"
#${SCOPE="all"}

# get window numbers, if the current window is the match,
# try to find the next one
#$SCRIPTPATH/screen-session dump -r $SCOPE |grep -E "^[0-9]* PID [0-9]* $*" | cut -d" " -f1 |\
w=$(
$SCRIPTPATH/screen-session dump -r $SCOPE |grep -E "^[0-9]* $*" | cut -d" " -f1 |\
{

    read w
    if [ "$w" = "`$SCREENBIN -p - -Q number | cut -d " " -f1`" ]; then
        w_alt="$w"

        while [ "$w" = "$w_alt" ]; do
            read w_alt
        done

        w="$w_alt"
    fi
    echo $w
}
)

if [ -z "$w" ]; then
    exit 1
fi

$SCREENBIN -X select $w

exit 0
