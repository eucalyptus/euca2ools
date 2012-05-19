#!/bin/sh -e

MANDIR=${MANDIR:-./man}

rm -rf "$MANDIR/"*
mkdir -p "$MANDIR"
export PYTHONPATH=".:$PYTHONPATH"

# eucacommand-based
for exe in bin/euca-*; do
    help2man "$exe" -N -o "$MANDIR/${exe##*/}.1" -n "$($exe --help | sed '/^$/,$d')"
done

# roboto-based
for exe in bin/euare-* bin/eustore-*; do
    help2man "$exe" -N -o "$MANDIR/${exe##*/}.1" -n "$($exe --help | sed '1,2d;/^$/,$d')"
done
