"""M2Crypto.SSL.Session client demo2: This program creates two sockets, each
bound to a different local address. The first creates an SSL connection, the
second then creates another SSL connection using the first's SSL session id.

(This program only works if you've ifconfig'ed your interfaces correctly,
of course.)

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved."""

from M2Crypto import Err, Rand, SSL, X509, threading
m2_threading = threading; del threading

import formatter, getopt, htmllib, sys
from threading import Thread
from socket import gethostname

ADDR1 = '127.0.0.1', 9999
ADDR2 = '127.0.0.2', 9999

def handler(addr, sslctx, host, port, req, sslsess=None):

    s = SSL.Connection(sslctx)
    s.bind(addr)
    if sslsess:
        s.set_session(sslsess)
        s.connect((host, port))
    else:
        s.connect((host, port))
        sslsess = s.get_session()
    s.write(req)
    while 1:
        data = s.read(4096)
        if not data:
            break

    if addr != ADDR2:
        thr = Thread(target=handler, 
                    args=(ADDR2, sslctx, host, port, req, sslsess))
        print "Thread =", thr.getName()
        thr.start()

    s.close()


if __name__ == '__main__':

    m2_threading.init()
    Rand.load_file('../randpool.dat', -1) 

    host = '127.0.0.1'
    port = 443
    req = '/'

    optlist, optarg = getopt.getopt(sys.argv[1:], 'h:p:r:')
    for opt in optlist:
        if '-h' in opt:
            host = opt[1]
        elif '-p' in opt:
            port = int(opt[1])
        elif '-r' in opt:
            req = opt[1]
    
    ctx = SSL.Context('sslv3')
    ctx.load_cert('client.pem')
    ctx.load_verify_info('ca.pem')
    ctx.set_verify(SSL.verify_none, 10)
    
    req = 'GET %s HTTP/1.0\r\n\r\n' % req

    start = Thread(target=handler, args=(ADDR1, ctx, host, port, req))
    print "Thread =", start.getName()
    start.start()
    start.join()
    
    m2_threading.cleanup()
    Rand.save_file('../randpool.dat')


