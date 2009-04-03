#!/usr/bin/env python

"""An M2Crypto implementation of OpenSSL's s_client.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from socket import *
import getopt
import string
import sys

from M2Crypto import SSL

# s_server -www
HOST='127.0.0.1'
PORT=4433
REQ='GET / HTTP/1.0\r\n\r\n'

class Config:
    pass

def config(args):
    options=['connect=', 'verify=', 'cert=', 'key=', 'CApath=', 'CAfile=', \
        'reconnect', 'pause', 'showcerts', 'debug', 'nbio_test', 'state', \
        'nbio', 'crlf', 'sslv2', 'sslv3', 'tlsv1', 'no_sslv2', 'no_sslv3', \
        'no_tlsv1', 'bugs', 'cipher=', 'Verify=']
    optlist, optarg=getopt.getopt(args, '', options)

    cfg=Config()
    for opt in optlist:
        setattr(cfg, opt[0][2:], opt[1])
    for x in (('tlsv1','no_tlsv1'),('sslv3','no_sslv3'),('sslv2','no_sslv2')):
        if hasattr(cfg, x[0]) and hasattr(cfg, x[1]):
                raise ValueError, 'mutually exclusive: %s and %s' % x

    if hasattr(cfg, 'connect'):
        (host, port)=string.split(cfg.connect, ':')
        cfg.connect=(host, int(port))
    else:
        cfg.connect=(HOST, PORT)

    cfg.protocol=[]
    # First protocol found will be used.
    # Permutate the following tuple for preference. 
    for p in ('tlsv1', 'sslv3', 'sslv2'):
        if hasattr(cfg, p):
            cfg.protocol.append(p)
    cfg.protocol.append('sslv23')

    return cfg

def make_context(config):
    ctx=SSL.Context(config.protocol[0])
    if hasattr(config, 'cert'):
        cert=config.cert
    else:
        cert='client.pem'
    if hasattr(config, 'key'):
        key=config.key
    else:
        key='client.pem'
    #ctx.load_cert(cert, key)

    if hasattr(config, 'verify'):
        verify=SSL.verify_peer
        depth=int(config.verify)
    elif hasattr(config, 'Verify'):
        verify=SSL.verify_peer | SSL.verify_fail_if_no_peer_cert
        depth=int(config.Verify)
    else:
        verify=SSL.verify_none
        depth=10
    config.verify=verify
    config.verify_depth=depth
    ctx.set_verify(verify, depth)

    if hasattr(config, 'CAfile'):
        cafile=config.CAfile
    else:
        cafile='ca.pem'
    ctx.load_verify_location(cafile)

    return ctx

def s_client(config):
    ctx=make_context(config)
    s=SSL.Connection(ctx)
    s.connect(config.connect)
    if config.verify != SSL.verify_none and not s.verify_ok():
        print 'peer verification failed'
        peer=s.get_peer_cert()
        if peer is None:
            print 'unable to get peer certificate'
        else:
            print 'peer.as_text()'
        raise SystemExit
    s.send(REQ)
    while 1:
        data=s.recv()
        if not data:
            break
        print data
    s.close()

if __name__=='__main__':
    cfg=config(sys.argv[1:])
    s_client(cfg)

