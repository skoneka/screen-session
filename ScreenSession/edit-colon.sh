#!/bin/sh
DIR="$SCSTMPDIR/___edit-colon"
mkdir -p "$DIR"
FILE="$DIR/$STY"
FILE_SOURCE="$FILE-source"
$EDITOR "$FILE"

if [ "$*" ]; then
    m4 $* "$FILE" > "$FILE_SOURCE"
    if ! cmp -s $FILE $FILE_SOURCE; then
        $EDITOR "$FILE_SOURCE"
    fi
else
    FILE_SOURCE="$FILE"
fi

$SCREENBIN -X source "$FILE_SOURCE"
