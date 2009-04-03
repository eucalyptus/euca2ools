#!/usr/bin/env python

# Standard Python library
import os
import os.path
import sys

# Medusa 
import asyncore
import default_handler
import filesys
import http_server
import status_handler

# M2Crypto
import https_server
import poison_handler
from M2Crypto import Rand, SSL

# XMLrpc
import xmlrpc_handler


HTTP_PORT=9080
HTTPS_PORT=9443

hs=http_server.http_server('', HTTP_PORT)

Rand.load_file('../randpool.dat', -1) 
ssl_ctx=SSL.Context('sslv23')
ssl_ctx.load_cert('server.pem')
#ssl_ctx.load_verify_location('ca.pem')
#ssl_ctx.load_client_CA('ca.pem')
#ssl_ctx.set_verify(SSL.verify_peer, 10)
#ssl_ctx.set_verify(SSL.verify_peer|SSL.verify_fail_if_no_peer_cert, 10)
#ssl_ctx.set_verify(SSL.verify_peer|SSL.verify_client_once, 10)
ssl_ctx.set_verify(SSL.verify_none, 10)
ssl_ctx.set_session_id_ctx('127.0.0.1:9443')
ssl_ctx.set_tmp_dh('dh1024.pem')
#ssl_ctx.set_info_callback()

hss=https_server.https_server('', HTTPS_PORT, ssl_ctx)

#fs=filesys.os_filesystem(os.path.abspath(os.curdir))
fs=filesys.os_filesystem('/usr/local/pkg/apache/htdocs')
#fs=filesys.os_filesystem('c:/pkg/jdk118/docs')
dh=default_handler.default_handler(fs)
hs.install_handler(dh)
hss.install_handler(dh)

# Cribbed from xmlrpc_handler.py.
# This is where you implement your RPC functionality.
class rpc_demo (xmlrpc_handler.xmlrpc_handler):
    def call (self, method, params):
        print 'method="%s" params=%s' % (method, params)
        return "Sure, that works"

rpch = rpc_demo()
hs.install_handler(rpch)
hss.install_handler(rpch)

ph=poison_handler.poison_handler(10)
hs.install_handler(ph)
hss.install_handler(ph)

sh=status_handler.status_extension([hss])
hs.install_handler(sh)
hss.install_handler(sh)

asyncore.loop()
Rand.save_file('../randpool.dat')

