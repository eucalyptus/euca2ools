"""Server demonstration of M2Crypto.xmlrpclib2.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

# M2Crypto
from M2Crypto import DH, SSL
from echod_lib import init_context

# /F's xmlrpcserver.py.
from xmlrpcserver import RequestHandler

class xmlrpc_handler(RequestHandler):
    def call(self, method, params):
        print "XMLRPC call:", method, params
        return params

    def finish(self):
        self.request.set_shutdown(SSL.SSL_RECEIVED_SHUTDOWN | SSL.SSL_SENT_SHUTDOWN)
        self.request.close()

if __name__ == '__main__':
    ctx = init_context('sslv23', 'server.pem', 'ca.pem', SSL.verify_none)
    ctx.set_tmp_dh('dh1024.pem')
    s = SSL.ThreadingSSLServer(('', 9443), xmlrpc_handler, ctx)
    s.serve_forever()   

