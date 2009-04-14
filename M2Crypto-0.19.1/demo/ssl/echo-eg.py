#!/usr/bin/env python

"""Demo SSL client #1 for the HOWTO.

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved."""

import getopt, sys
from socket import gethostname
from M2Crypto import Err, Rand, SSL, X509, threading

host = '127.0.0.1'
port = 9999

optlist, optarg = getopt.getopt(sys.argv[1:], 'h:p:')
for opt in optlist:
    if '-h' in opt:
        host = opt[1]
    elif '-p' in opt:
        port = int(opt[1])

Rand.load_file('../randpool.dat', -1) 

ctx = SSL.Context('sslv3')
ctx.load_cert('client.pem')
#ctx.load_verify_info('ca.pem')
ctx.set_verify(SSL.verify_peer, 10)
ctx.set_info_callback()

s = SSL.Connection(ctx)
s.connect((host, port))
print 'Host =', gethostname()
print 'Cipher =', s.get_cipher().name()

peer = s.get_peer_cert()
print 'Server =', peer.get_subject().CN

while 1:
    data = s.recv()
    if not data:
        break
    sys.stdout.write(data)
    sys.stdout.flush()
    buf = sys.stdin.readline()
    if not buf: 
        break
    s.send(buf)

s.close()

Rand.save_file('../randpool.dat')

