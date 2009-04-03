#!/usr/bin/env python

"""Demonstrations of M2Crypto.httpslib.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

import sys
from M2Crypto import Rand, SSL, httpslib, threading


def test_httpslib():
    ctx = SSL.Context('sslv23')
    ctx.load_cert_chain('client.pem')
    ctx.load_verify_locations('ca.pem', '')
    ctx.set_verify(SSL.verify_peer, 10)        
    ctx.set_info_callback()
    h = httpslib.HTTPSConnection('localhost', 19443, ssl_context=ctx)
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
        #data = f.readline(4096)   
        data = resp.read(4096)
        if not data: break
        c = c + len(data)
        #print data
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

