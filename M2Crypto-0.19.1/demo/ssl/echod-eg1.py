#!/usr/bin/env python

"""Demo SSL server #1 for the HOWTO.

Copyright (c) 1999-2001 Ng Pheng Siong. All rights reserved."""

import SocketServer
from M2Crypto import Err, Rand, SSL, threading

def init_context(protocol, dhpfile, certfile, cafile, verify, verify_depth=10):
    ctx = SSL.Context(protocol)
    ctx.set_tmp_dh(dhpfile)
    ctx.load_cert(certfile)
    #ctx.load_verify_info(cafile)
    ctx.set_verify(verify, verify_depth)
    ctx.set_session_id_ctx('echod')
    ctx.set_info_callback()
    return ctx

class ssl_echo_handler(SocketServer.BaseRequestHandler):

    buffer = 'Ye Olde Echo Servre\r\n'

    def handle(self):
        peer = self.request.get_peer_cert()
        if peer is not None:
            print 'Client CA        =', peer.get_issuer().O
            print 'Client Subject   =', peer.get_subject().CN
        self.request.write(self.buffer)
        while 1:
            buf = self.request.read()
            if not buf:
                break
            self.request.write(buf) 

    def finish(self):
        self.request.set_shutdown(SSL.SSL_SENT_SHUTDOWN|SSL.SSL_RECEIVED_SHUTDOWN)
        self.request.close()

if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1) 
    threading.init()
    ctx = init_context('sslv23', 'dh1024.pem', 'server.pem', 'ca.pem', SSL.verify_peer)
    s = SSL.SSLServer(('', 9999), ssl_echo_handler, ctx)
    s.serve_forever()   
    threading.cleanup()
    Rand.save_file('randpool.dat')


