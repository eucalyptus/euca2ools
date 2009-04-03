#!/usr/bin/env python

"""An M2Crypto implementation of OpenSSL's s_server.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from socket import *
import asyncore
import cStringIO
import getopt
import string
import sys

from M2Crypto import SSL, BIO, DH, Err

# s_server -www
HOST=''
PORT=4433

class Config:
    pass

def config(args):
    options=['accept=', 'context=', 'verify=', 'Verify=', 'cert=', 'key=', \
        'dcert=', 'dkey=', 'nocert', 'crlf', 'debug', 'CApath=', 'CAfile=', \
        'quiet', 'no_tmp_rsa', 'state', 'sslv2', 'sslv3', 'tlsv1', \
        'no_sslv2', 'no_sslv3', 'no_tlsv1', 'bugs', 'cipher=']
    optlist, optarg=getopt.getopt(args, '', options)

    cfg=Config()
    for opt in optlist:
        setattr(cfg, opt[0][2:], opt[1])
    for x in (('tlsv1','no_tlsv1'),('sslv3','no_sslv3'),('sslv2','no_sslv2')):
        if hasattr(cfg, x[0]) and hasattr(cfg, x[1]):
                raise ValueError, 'mutually exclusive: %s and %s' % x

    if hasattr(cfg, 'accept'):
        cfg.accept=string.split(cfg.connect, ':')
    else:
        cfg.accept=(HOST, PORT)

    cfg.protocol=[]
    # First protocol found will be used.
    # Permutate the following tuple for preference. 
    for p in ('tlsv1', 'sslv3', 'sslv2'):
        if hasattr(cfg, p):
            cfg.protocol.append(p)
    cfg.protocol.append('sslv23')

    return cfg

RESP_HEAD="""\
HTTP/1.0 200 ok
Content-type: text/html

<HTML><BODY BGCOLOR=\"#ffffff\">
<pre>

Emulating s_server -www
Ciphers supported in s_server.py
"""

RESP_TAIL="""\
</pre>
</BODY></HTML>
"""

class channel(SSL.ssl_dispatcher):

    def __init__(self, conn, debug):
        SSL.ssl_dispatcher.__init__(self, conn)
        self.socket.setblocking(0)
        self.buffer=self.fixup_buffer()
        self.debug=debug

    def fixup_buffer(self):
        even=0
        buffer=cStringIO.StringIO()
        buffer.write(RESP_HEAD)
        for c in self.get_ciphers():
            # This formatting works for around 80 columns.
            buffer.write('%-11s:%-28s' % (c.version(), c.name()))
            if even:
                buffer.write('\r\n')
                even=1-even
        buffer.write('\r\n%s' % RESP_TAIL)
        return buffer.getvalue()

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_error(self, exc_type, exc_value, exc_traceback):
        if self.debug:
            print 'handle_error()'
        #print exc_type, exc_value, exc_traceback
        print Err.get_error()
        self.handle_close()


    def writeable(self):
        return len(self.buffer)

    def handle_write(self):
        n=self.send(self.buffer)
        if n==-1:
            pass
        elif n==0:
            self.handle_close()
        else:
            self.buffer=self.buffer[n:]
        if self.debug:
            print 'handle_write():', n

    def readable(self):
        return 1

    def handle_read(self):
        blob=self.recv()
        if blob is None:
            pass
        elif blob=='':
            self.handle_close() 
        else: 
            pass
        if self.debug:
            print 'handle_read():', blob


class server(SSL.ssl_dispatcher):

    channel_class=channel

    def __init__(self, addr, port, config, ssl_context):
        asyncore.dispatcher.__init__(self)
        self.create_socket(ssl_context)
        self.set_reuse_addr()
        self.socket.setblocking(0)
        self.bind((addr, port))
        self.listen(5)
        self.config=config
        self.debug=config.debug
        self.ssl_ctx=ssl_context

    def handle_accept(self):
        sock, addr=self.accept()
        print self.ssl_ctx.get_verify_mode()
        if (self.ssl_ctx.get_verify_mode() is SSL.verify_none) or sock.verify_ok():
            self.channel_class(sock, self.debug)
        else:
            print 'client verification failed'
            sock.close()

    def writeable(self):
        return 0

def s_server(config):
    ctx=SSL.Context(config.protocol[0])

    if hasattr(config, 'debug'):
        config.debug=1
    else:
        config.debug=0

    if hasattr(config, 'cert'):
        cert=config.cert
    else:
        cert='server.pem'
    if hasattr(config, 'key'):
        cert=config.key
    else:
        cert='server.pem'
    ctx.load_cert(cert)

    if hasattr(config, 'CAfile'):
        cafile=config.CAfile
    else:
        cafile='ca.pem'
    ctx.load_verify_location(cafile)

    if hasattr(config, 'verify'):
        verify=SSL.verify_peer
        depth=int(config.verify)
    elif hasattr(config, 'Verify'):
        verify=SSL.verify_peer | SSL.verify_fail_if_no_peer_cert
        depth=int(config.Verify)
    else:
        verify=SSL.verify_none
        depth=0
    ctx.set_verify(verify, depth)

    ctx.set_tmp_dh('dh1024.pem')
    #ctx.set_info_callback()

    server(cfg.accept[0], cfg.accept[1], cfg, ctx)
    asyncore.loop()

if __name__=='__main__':
    cfg=config(sys.argv[1:])
    s_server(cfg)

