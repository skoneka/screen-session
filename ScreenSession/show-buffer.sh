#!/bin/sh
# need writereg command

cleanup() {
    rm -f $FILE
}
trap cleanup 1 2 3 6 15

DIR="$SCSTMPDIR/___registers/_$STY_"
FILE=$DIR"/\."
mkdir -p $DIR
$SCREENBIN -X writebuf "$FILE"
$SCREENBIN -Q echo "Printing copy buffer." > /dev/null
cat "$FILE"
cleanup
