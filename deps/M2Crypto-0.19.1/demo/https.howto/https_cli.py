#!/usr/bin/env python

"""Demonstrations of M2Crypto.httpslib.

Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved.

Portions created by Open Source Applications Foundation (OSAF) are
Copyright (C) 2006 OSAF. All Rights Reserved.
"""

import sys
from M2Crypto import Rand, SSL, httpslib, threading


def test_httpslib():
    ctx = SSL.Context()
    if ctx.load_verify_locations('ca.pem') != 1:
        raise Exception('CA certificates not loaded')
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
    ctx.set_info_callback()
    h = httpslib.HTTPSConnection('localhost', 9443, ssl_context=ctx)
    h.set_debuglevel(1)
    h.putrequest('GET', '/')
    h.putheader('Accept', 'text/html')
    h.putheader('Accept', 'text/plain')
    h.putheader('Connection', 'close')
    h.endheaders()
    resp = h.getresponse()
    f = resp.fp
    c = 0
    while 1:
        # Either of following two works.
        #data = f.readline()   
        data = resp.read()
        if not data: break
        c = c + len(data)
        sys.stdout.write(data)
        sys.stdout.flush()
    f.close()
    h.close()


if __name__=='__main__':
    Rand.load_file('../randpool.dat', -1) 
    #threading.init()
    test_httpslib()
    #threading.cleanup()
    Rand.save_file('../randpool.dat')

