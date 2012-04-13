#!/bin/sh -e

mkdir -p man
rm -rf man/*
export PYTHONPATH=".:$PYTHONPATH"

# eucacommand-based
for exe in bin/euca-*; do
    help2man "$exe" -N -o "man/$(basename $exe).1" -n "$($exe --help | sed '/^$/,$d')"
done

# roboto-based
for exe in bin/euare-*; do
    help2man "$exe" -N -o "man/$(basename $exe).1" -n "$($exe --help | sed '1,2d;/^$/,$d')"
done
