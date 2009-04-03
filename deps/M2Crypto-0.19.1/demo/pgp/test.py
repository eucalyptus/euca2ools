
#!/usr/bin/env python

"""PGP test program.

Copyright (c) 1999 Ng Pheng Siong. All rights reserved."""

from M2Crypto import EVP, PGP
from cStringIO import StringIO

def test1():
    pkr = PGP.load_pubring('pubring.pgp')
    daft = pkr['daft']
    daft_pkt = daft._pubkey_pkt.pack()
    s1 = EVP.MessageDigest('sha1')
    s1.update(daft_pkt)
    print `s1.final()`

    buf = StringIO(daft_pkt)
    ps = PGP.packet_stream(buf)
    dift_pkt = ps.read()
    s2 = EVP.MessageDigest('sha1')
    s2.update(dift_pkt.pack())
    print `s2.final()`

if __name__ == '__main__':
    test1()

