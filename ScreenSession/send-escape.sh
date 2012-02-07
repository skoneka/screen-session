#!/bin/sh
#echo -n '\033P\033]12;red\007\033\\'
#echo -n '\033P\033]12;orange\007\033\\'

if [ -n "$STY" ]; then
    A='\033P'
    B='\033\\'
    echo -n $A$1$B
else
    echo -n $1
fi
