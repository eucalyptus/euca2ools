#!/bin/sh -e

mkdir -p man
rm -rf man/*
export PYTHONPATH=".:$PYTHONPATH"

# eucacommand-based
for exe in build/*/euca-*; do
    help2man "$exe" -N -o "man/$(basename $exe).1" -n "$($exe --help | sed '/^$/,$d')"
done

# roboto-based
for exe in build/*/euare-* build/*/eustore-*; do
    help2man "$exe" -N -o "man/$(basename $exe).1" -n "$($exe --help | sed '1,2d;/^$/,$d')"
done
