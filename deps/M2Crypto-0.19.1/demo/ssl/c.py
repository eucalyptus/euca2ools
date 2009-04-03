#!/usr/bin/env python

"""C programming in Python. Have SWIG sweat the pointers. ;-)

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

from socket import *
import sys

from M2Crypto import SSL, m2

HOST = '127.0.0.1'
PORT = 9443
req_10 = 'GET / HTTP/1.0\r\n\r\n'
req_11 = 'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'


def c_10():
    c_style(HOST, PORT, req_10) 


def c_11():
    c_style(HOST, PORT, req_11) 


def c_style(HOST, PORT, req):

    # Set up SSL context.
    ctx = m2.ssl_ctx_new(m2.sslv3_method())
    m2.ssl_ctx_use_cert(ctx, 'client.pem')
    m2.ssl_ctx_use_privkey(ctx, 'client.pem')

    # Make the socket connection.
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((HOST, PORT))

    # Set up the SSL connection.
    sbio = m2.bio_new_socket(s.fileno(), 0)
    ssl = m2.ssl_new(ctx)
    m2.ssl_set_bio(ssl, sbio, sbio)
    m2.ssl_connect(ssl)
    sslbio = m2.bio_new(m2.bio_f_ssl())
    m2.bio_set_ssl(sslbio, ssl, 0)

    # Push a buffering BIO over the SSL BIO.
    iobuf = m2.bio_new(m2.bio_f_buffer())
    topbio = m2.bio_push(iobuf, sslbio)

    # Send the request.
    m2.bio_write(sslbio, req)

    # Receive the response.
    while 1:
        data = m2.bio_gets(topbio, 4096)
        if not data: break
        sys.stdout.write(data)

    # Cleanup. May be missing some necessary steps. ;-|
    m2.bio_pop(topbio)
    m2.bio_free(iobuf)
    m2.ssl_shutdown(ssl)
    m2.ssl_free(ssl)
    m2.ssl_ctx_free(ctx)
    s.close()


if __name__ == '__main__':
    c_10()
    c_11()

