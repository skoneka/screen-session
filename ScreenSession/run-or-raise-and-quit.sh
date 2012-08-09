#!/bin/sh
SCRIPTPATH=$(dirname $(realpath $0))

A="PID [0-9]* CMD"
for arg in "$@"
do
    A=$A" \"?"$arg"\"?"
done

$SCRIPTPATH/raise-window.sh "$A"

if [ $? -eq 1 ]; then
    $SCREENBIN -X echo "unable to raise - starting a new instance"
    exec "$@"
else
    $SCREENBIN -p $WINDOW -X kill
    exit 0
fi

