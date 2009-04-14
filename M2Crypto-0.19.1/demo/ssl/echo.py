#!/usr/bin/env python

"""A simple SSL 'echo' client.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

import getopt, sys
from socket import gethostname
from M2Crypto import Err, Rand, SSL, X509

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
ctx.load_cert_chain('client.pem')
#ctx.set_verify(SSL.verify_none, 10)
ctx.set_verify(SSL.verify_peer, 10, SSL.cb.ssl_verify_callback)
ctx.load_verify_locations('ca.pem')
#ctx.set_allow_unknown_ca(1)
ctx.set_info_callback()

s = SSL.Connection(ctx)
s.connect((host, port))
print 'Host =', gethostname()
print 'Cipher =', s.get_cipher().name()

## 2003-06-28, ngps: Depends on ctx.set_verify() above, RTFM for details.
## v = s.get_verify_result()
## if v != X509.V_OK:
##     s.close()
##     raise SystemExit, 'Server verification failed'

peer = s.get_peer_cert()
print 'Server =', str(peer.get_subject())

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

