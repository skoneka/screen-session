#!/bin/sh
# need writereg command

cleanup() {
    rm -f $FILE
}
trap cleanup 1 2 3 6 15

DIR="$SCSTMPDIR/___registers/$STY"
FILE=$DIR"/\."
mkdir -p $DIR
$SCREENBIN -X writebuf "$FILE"
$SCREENBIN -Q echo "Editing copy buffer."
$EDITOR $FILE
$SCREENBIN -X readbuf "$FILE"
$SCREENBIN -Q echo "Finished editing copy buffer."
cleanup
#$SCREENBIN -p $WINDOW -X eval "kill"
