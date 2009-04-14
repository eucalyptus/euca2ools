#!/usr/bin/env python
"""Unit tests for M2Crypto.BIO.File.

Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved."""

import unittest, threading, sys, socket

from M2Crypto import BIO 
from M2Crypto import SSL 
from M2Crypto import Err
from M2Crypto import Rand
from M2Crypto import threading as m2threading

from test_ssl import srv_host, srv_port

class HandshakeClient(threading.Thread):
    
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        
    def run(self):
        ctx = SSL.Context()
        ctx.load_cert_chain("tests/server.pem") 
        conn = SSL.Connection(ctx)
        cipher_list = conn.get_cipher_list()
        sslbio = BIO.SSLBio()
        readbio = BIO.MemoryBuffer()
        writebio = BIO.MemoryBuffer()
        sslbio.set_ssl(conn)
        conn.set_bio(readbio, writebio)
        conn.set_connect_state()
        sock = socket.socket()
        sock.connect((self.host, self.port))
        
        handshake_complete = False
        while not handshake_complete:
            ret = sslbio.do_handshake()
            if ret <= 0: 
                if not sslbio.should_retry() or not sslbio.should_read():
                    err_string = Err.get_error() 
                    print err_string
                    sys.exit("unrecoverable error in handshake - client")
                else:
                     output_token  = writebio.read()
                     if output_token is not None:
                         sock.sendall(output_token)
                     else: 
                         input_token = sock.recv(1024)
                         readbio.write(input_token) 
            else:
                handshake_complete = True 
       
        sock.close()


class SSLTestCase(unittest.TestCase):
    
    def setUp(self):
        self.sslbio = BIO.SSLBio()
    
    def test_pass(self): # XXX leaks 64/24 bytes
        pass

    def test_set_ssl(self): # XXX leaks 64/1312 bytes
        ctx = SSL.Context()
        conn = SSL.Connection(ctx)
        self.sslbio.set_ssl(conn)

    def test_do_handshake_fail(self): # XXX leaks 64/42066 bytes
        ctx = SSL.Context()
        conn = SSL.Connection(ctx)
        conn.set_connect_state()
        self.sslbio.set_ssl(conn)
        ret = self.sslbio.do_handshake() 
        assert ret == 0 

    def test_should_retry_fail(self): # XXX leaks 64/1312 bytes
        ctx = SSL.Context()
        conn = SSL.Connection(ctx) 
        self.sslbio.set_ssl(conn)
        ret = self.sslbio.do_handshake() 
        assert ret == -1 
        ret = self.sslbio.should_retry() 
        assert ret == 0 
    
    def test_should_write_fail(self): # XXX leaks 64/1312 bytes
        ctx = SSL.Context()
        conn = SSL.Connection(ctx) 
        self.sslbio.set_ssl(conn)
        ret = self.sslbio.do_handshake() 
        assert ret == -1 
        ret = self.sslbio.should_write() 
        assert ret == 0 
    
    def test_should_read_fail(self): # XXX leaks 64/1312 bytes
        ctx = SSL.Context()
        conn = SSL.Connection(ctx)
        self.sslbio.set_ssl(conn)
        ret = self.sslbio.do_handshake() 
        assert ret == -1 
        ret = self.sslbio.should_read() 
        assert ret == 0 
   
    def test_do_handshake_succeed(self): # XXX leaks 196/26586 bytes
        ctx = SSL.Context() 
        ctx.load_cert_chain("tests/server.pem")
        conn = SSL.Connection(ctx) 
        self.sslbio.set_ssl(conn)
        readbio = BIO.MemoryBuffer()
        writebio = BIO.MemoryBuffer()
        conn.set_bio(readbio, writebio)
        conn.set_accept_state()
        handshake_complete = False
        sock = socket.socket()
        sock.bind((srv_host, srv_port))
        sock.listen(5)
        handshake_client = HandshakeClient(srv_host, srv_port)
        handshake_client.start() 
        new_sock, addr = sock.accept()
        while not handshake_complete:
            input_token = new_sock.recv(1024)
            readbio.write(input_token)

            ret = self.sslbio.do_handshake()
            if ret <= 0:
                if not self.sslbio.should_retry() or not self.sslbio.should_read():
                    sys.exit("unrecoverable error in handshake - server")
            else:
                handshake_complete = True

            output_token  = writebio.read()
            if output_token is not None:
                new_sock.sendall(output_token)
      
        handshake_client.join() 
        sock.close() 
        new_sock.close() 

def suite(): 
    return unittest.makeSuite(SSLTestCase)
    

if __name__ == '__main__':
    Rand.load_file('randpool.dat', -1)
    m2threading.init()
    unittest.TextTestRunner().run(suite())
    m2threading.cleanup()
    Rand.save_file('randpool.dat')
