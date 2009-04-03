#!/usr/bin/env python

"""A multi-threading SSL 'echo' server.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from M2Crypto import DH, Rand, SSL, threading
import echod_lib

class ssl_echo_handler(echod_lib.ssl_echo_handler):

    buffer='Ye Olde Threading Echo Servre\r\n'

    def finish(self):
        # Threading servers need this.
        self.request.set_shutdown(SSL.SSL_SENT_SHUTDOWN|SSL.SSL_RECEIVED_SHUTDOWN)
        self.request.close()


if __name__=='__main__':
    try:
        threading.init()
        Rand.load_file('../randpool.dat', -1) 
        ctx=echod_lib.init_context('sslv23', 'server.pem', 'ca.pem', 
            SSL.verify_peer | SSL.verify_fail_if_no_peer_cert)
        ctx.set_tmp_dh('dh1024.pem')
        s=SSL.ThreadingSSLServer(('', 9999), ssl_echo_handler, ctx)
        s.serve_forever()   
        Rand.save_file('../randpool.dat')
    except:
        threading.cleanup()

