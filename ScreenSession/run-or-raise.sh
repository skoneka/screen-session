#!/bin/sh
# raise a GNU Screen window or run the command
# run-or-raise.sh [command]
# run-or-raise.sh vi config

SCRIPTPATH=$(dirname $(realpath $0))

A="PID [0-9]* CMD"
for arg in "$@"
do
    A=$A" \"?"$arg"\"?"
done
echo $A
$SCRIPTPATH/raise-window.sh "$A"

if [ $? -eq 1 ]; then
    $SCREENBIN -X echo "unable to raise - starting a new instance"
    exec "$@"
else
    $SCREENBIN -X echo "raised"
    exit 0
fi

