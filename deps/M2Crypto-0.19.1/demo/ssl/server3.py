#!/usr/bin/env python
"""
server3 from the book 'Network Security with OpenSSL', but modified to
Python/M2Crypto from the original C implementation.

Copyright (c) 2004-2005 Open Source Applications Foundation.
Author: Heikki Toivonen
"""
from M2Crypto import SSL, Rand, threading, DH
import thread
from socket import *

verbose_debug = 1

def verify_callback(ok, store):
    if not ok:
        print "***Verify Not ok"
    return ok

dh1024 = None

def init_dhparams():
    global dh1024
    dh1024 = DH.load_params('dh1024.pem')

def tmp_dh_callback(ssl, is_export, keylength):
    global dh1024
    if not dh1024:
        init_dhparams()
    return dh1024._ptr()

def setup_server_ctx():
    ctx = SSL.Context('sslv23')
    if ctx.load_verify_locations('ca.pem') != 1:
        print "***No CA file"
    #if ctx.set_default_verify_paths() != 1:
    #    print "***No default verify paths"
    ctx.load_cert_chain('server.pem')
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                   10, verify_callback)
    ctx.set_options(SSL.op_all | SSL.op_no_sslv2)
    ctx.set_tmp_dh_callback(tmp_dh_callback)
    #ctx.set_tmp_dh('dh1024.pem')
    if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
        print "***No valid ciphers"
    if verbose_debug:
        ctx.set_info_callback()
    return ctx

def post_connection_check(peerX509, expectedHost):
    if peerX509 is None:
        print "***No peer certificate"
    # Not sure if we can do any other checks
    return 1

def do_server_loop(conn):
    while 1:
        try:
            buf = conn.read()
            if not buf:
                break
            print buf
        except SSL.SSLError, what:
            if str(what) == 'unexpected eof':
                break
            else:
                raise
        except:
            break
            
    if conn.get_shutdown():
        return 1
    return 0

# How about something like:
#def server_thread(ctx, ssl, addr):
#    conn = SSL.Connection(ctx, None)
#    conn.ssl = ssl
#    conn.setup_addr(addr)
def server_thread(ctx, sock, addr):
    conn = SSL.Connection(ctx, sock)
    conn.set_post_connection_check_callback(post_connection_check)
    conn.setup_addr(addr)
    conn.set_accept_state()
    conn.setup_ssl()
    conn.accept_ssl()
    
    post_connection_check(conn)

    print 'SSL Connection opened'
    if do_server_loop(conn):
        conn.close()
    else:
        conn.clear()
    print 'SSL Connection closed'        
    

if __name__=='__main__':
    threading.init()
    Rand.load_file('../randpool.dat', -1) 

    ctx = setup_server_ctx()

    # How about something like this?
    #conn_root = SSL.Connection(ctx)
    #conn_root.bind(('127.0.0.1', 9999))
    #conn_root.listen(5)
    #while 1:
    #    ssl, addr = conn_root.accept()
    #    thread.start_new_thread(server_thread, (ctx, ssl, addr))

    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('', 9999))
    sock.listen(5)
    while 1:
        conn, addr = sock.accept()
        thread.start_new_thread(server_thread, (ctx, conn, addr))
 
    Rand.save_file('../randpool.dat')
    threading.cleanup()
