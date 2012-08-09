#!/bin/sh
SCRIPTPATH=$(dirname $(realpath $0)); cd $SCRIPTPATH || exit 1;

[ "$SCOPE" ] || SCOPE="all"

# get window numbers, if the current window is the match,
# try to find the next one
g=$(
$SCRIPTPATH/screen-session dump -Pr $SCOPE |
grep -E "^[0-9]* GRP [0-9]* $*"| cut -d" " -f3 |
{
    read g_c
    g_alt="$g_c"

    while [ "$g_c" = "$g_alt" ]; do
        read g_alt
    done

    g_c="$g_alt"
    echo $g_c
}
)

#<<
if [ -z "$g" ]; then
    exit 1
fi

$SCREENBIN -X select $g

exit 0
