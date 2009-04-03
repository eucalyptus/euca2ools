#!/usr/bin/env python

"""An asyncore-based SSL 'echo' server.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

import asyncore, errno, socket, time
from M2Crypto import Rand, SSL
import echod_lib

class ssl_echo_channel(asyncore.dispatcher):

    buffer = 'Ye Olde Echo Servre\r\n'

    def __init__(self, conn):
        asyncore.dispatcher.__init__(self, conn)
        self._ssl_accepting = 1
        self.peer = self.get_peer_cert()

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def writable(self):
        return self._ssl_accepting or (len(self.buffer) > 0)
 
    def handle_write(self):
        if self._ssl_accepting: 
            s = self.socket.accept_ssl()
            if s:
                self._ssl_accepting = 0
        else:
            try:
                n = self.send(self.buffer)
                if n == -1:
                    pass
                elif n == 0:
                    self.handle_close()
                else:
                    self.buffer = self.buffer[n:]
            except SSL.SSLError, what:
                if str(what) == 'unexpected eof':
                    self.handle_close()
                    return
                else:
                    raise

    def readable(self):
        return 1

    def handle_read(self):
        if self._ssl_accepting:
            s = self.socket.accept_ssl()
            if s:
                self._ssl_accepting = 0
        else:
            try:
                blob = self.recv(4096)
                if blob is None:
                    pass
                elif blob == '':
                    self.handle_close()
                else: 
                    self.buffer = self.buffer + blob        
            except SSL.SSLError, what:
                if str(what) == 'unexpected eof':
                    self.handle_close()
                    return
                else:
                    raise


class ssl_echo_server(SSL.ssl_dispatcher):

    channel_class=ssl_echo_channel

    def __init__(self, addr, port, ssl_context):
        SSL.ssl_dispatcher.__init__(self)
        self.create_socket(ssl_context)
        self.set_reuse_addr()
        self.socket.setblocking(0)
        self.bind((addr, port))
        self.listen(5)
        self.ssl_ctx=ssl_context
    
    def handle_accept(self):
        try:
            sock, addr = self.socket.accept()
            self.channel_class(sock)
        except:
            print '-'*40
            import traceback
            traceback.print_exc()
            print '-'*40
            return

    def writable(self):
        return 0


if __name__=='__main__':
    Rand.load_file('../randpool.dat', -1) 
    ctx = echod_lib.init_context('sslv23', 'server.pem', 'ca.pem', \
            #SSL.verify_peer | SSL.verify_fail_if_no_peer_cert)
            SSL.verify_none)
    ctx.set_tmp_dh('dh1024.pem')
    ssl_echo_server('', 9999, ctx)
    asyncore.loop()
    Rand.save_file('../randpool.dat')

