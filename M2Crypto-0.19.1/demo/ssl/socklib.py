"""
socklib provides a way to transparently replace socket.ssl with
M2Crypto.SSL.Connection.

Usage: Import socklib before the 3rd party module that uses socket.ssl. Also,
       call socketlib.setSSLContextFactory() to set it up with a way to get
       secure SSL contexts.

Copyright (c) 2007 Open Source Applications Foundation.
All rights reserved.
"""

sslContextFactory = None

def setSSLContextFactory(factory):
    global sslContextFactory
    sslContextFactory = factory

from M2Crypto.SSL import Connection, Checker
import socket

class ssl_socket(socket.socket):
    def connect(self, addr, *args):
        self.addr = addr
        return super(ssl_socket, self).connect(addr, *args)
        
    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
        socket.socket.close(self)

def ssl(sock):
    sock.conn = Connection(ctx=sslContextFactory(), sock=sock)
    sock.conn.addr = sock.addr
    sock.conn.setup_ssl()
    sock.conn.set_connect_state()
    sock.conn.connect_ssl()
    check = getattr(sock.conn, 'postConnectionCheck', sock.conn.clientPostConnectionCheck)
    if check is not None:
        if not check(sock.conn.get_peer_cert(), sock.conn.addr[0]):
            raise Checker.SSLVerificationError, 'post connection check failed'
    return sock.conn

socket.socket = ssl_socket
socket.ssl = ssl

