#!/bin/sh -e

[ -z "$PREFIX" ] && PREFIX="/usr/local"
[ -z "$MANDIR" ] && MANDIR="$PREFIX/share/man"

install -d "$DESTDIR/$MANDIR/man1"
for manpage in man/*; do
    install "$manpage" "$DESTDIR/$MANDIR/man1/`basename $manpage`"
done
