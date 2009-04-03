#!/usr/bin/env python
"""Demonstrations of M2Crypto.httpslib.

Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved.

Portions created by Open Source Applications Foundation (OSAF) are
Copyright (C) 2006 OSAF. All Rights Reserved.
"""

from M2Crypto import Rand, SSL, httpslib

def get_https():
    ctx = SSL.Context()
    if ctx.load_verify_locations('ca.pem') != 1:
        raise Exception('CA certificates not loaded')
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
    h = httpslib.HTTPSConnection('localhost', 9443, ssl_context=ctx)
    h.set_debuglevel(1)
    h.putrequest('GET', '/')
    h.endheaders()
    resp = h.getresponse()
    while 1:
        data = resp.read()
        if not data: 
            break
        print data
    h.close()

Rand.load_file('../randpool.dat', -1) 
get_https()
Rand.save_file('../randpool.dat')

