#!/bin/sh -ex

mkdir -p man
export PYTHONPATH=".:$PYTHONPATH"

version="$(build/*/euca-version 2>&1 | sed -e 's/^euca2ools *\([^(]*\).*/\1/' -e 's/ *$//')"

for exe in $@; do
    description="$(build/*/$exe --help 2>&1 | python -c 'import sys; print sys.stdin.read().split("\n\n")[1]')"
    #version="$(build/*/$exe --version 2>&1 | sed -e 's/^euca2ools *\([^(]*\).*/\1/' -e 's/ *$//')"
    help2man -N --no-discard-stderr -S "euca2ools $version" -n "$description" --version-string "$version" -o man/$(basename $exe).1 build/*/$exe
    sed -i -e 's/^.SH DESCRIPTION/.SH SYNOPSIS/' \
           -e 's/usage: *//' \
           -e '/^\.IP/{/^\.IP/d}' \
           -e '/^\.PP/{s/^\.PP.*/.SH DESCRIPTION/}' \
           man/$(basename $exe).1
done
