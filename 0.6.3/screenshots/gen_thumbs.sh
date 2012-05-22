#!/bin/sh

WIDTH=384
HEIGHT=288

mkdir -p thumbs

for f in *.png; do etu -f $f -w $WIDTH -h $HEIGHT -o thumbs/$f; done
