"""M2Crypto.SSL.Session client demo: This program requests a URL from 
a HTTPS server, saves the negotiated SSL session id, parses the HTML 
returned by the server, then requests each HREF in a separate thread 
using the saved SSL session id.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import Err, Rand, SSL, X509, threading
m2_threading = threading; del threading

import formatter, getopt, htmllib, sys
from threading import Thread
from socket import gethostname


def handler(sslctx, host, port, href, recurs=0, sslsess=None):

    s = SSL.Connection(sslctx)
    if sslsess:
        s.set_session(sslsess)
        s.connect((host, port))
    else:
        s.connect((host, port))
        sslsess = s.get_session()
    #print sslsess.as_text()

    if recurs:
        p = htmllib.HTMLParser(formatter.NullFormatter())

    f = s.makefile("rw")
    f.write(href)
    f.flush()

    while 1:
        data = f.read()
        if not data:
            break
        if recurs:
            p.feed(data)

    if recurs:
        p.close()

    f.close()

    if recurs:
        for a in p.anchorlist:
            req = 'GET %s HTTP/1.0\r\n\r\n' % a
            thr = Thread(target=handler, 
                        args=(sslctx, host, port, req, recurs-1, sslsess))
            print "Thread =", thr.getName()
            thr.start()
    

if __name__ == '__main__':

    m2_threading.init()
    Rand.load_file('../randpool.dat', -1) 

    host = '127.0.0.1'
    port = 9443
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
    ctx.load_client_ca('ca.pem')
    ctx.set_verify(SSL.verify_none, 10)
    
    req = 'GET %s HTTP/1.0\r\n\r\n' % req

    start = Thread(target=handler, args=(ctx, host, port, req, 1))
    print "Thread =", start.getName()
    start.start()
    start.join()
    
    m2_threading.cleanup()
    Rand.save_file('../randpool.dat')


