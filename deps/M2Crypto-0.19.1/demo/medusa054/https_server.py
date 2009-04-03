#!/usr/bin/env python

"""A https server built on Medusa's http_server. 

Copyright (c) 1999-2004 Ng Pheng Siong. All rights reserved."""

import asynchat, asyncore, http_server, socket, sys
from M2Crypto import SSL, version

VERSION_STRING=version

class https_channel(http_server.http_channel):

    ac_in_buffer_size = 1 << 16

    def __init__(self, server, conn, addr):
        http_server.http_channel.__init__(self, server, conn, addr)

    def send(self, data):
        try:
            result = self.socket._write_nbio(data)
            if result <= 0:
                return 0
            else:
                self.server.bytes_out.increment(result)
                return result
        except SSL.SSLError, why:
            self.close()
            self.log_info('send: closing channel %s %s' % (repr(self), why))
            return 0

    def recv(self, buffer_size):
        try:
            result = self.socket._read_nbio(buffer_size)
            if result is None:
                return ''
            elif result == '':
                self.close()
                return ''
            else:
                self.server.bytes_in.increment(len(result))
                return result
        except SSL.SSLError, why:
            self.close()
            self.log_info('recv: closing channel %s %s' % (repr(self), why))
            return ''


class https_server(http_server.http_server):

    SERVER_IDENT='M2Crypto HTTPS Server (v%s)' % VERSION_STRING

    channel_class=https_channel

    def __init__(self, ip, port, ssl_ctx, resolver=None, logger_object=None):
        http_server.http_server.__init__(self, ip, port, resolver, logger_object)
        sys.stdout.write(self.SERVER_IDENT + '\n\n')
        sys.stdout.flush()
        self.ssl_ctx=ssl_ctx
        
    def handle_accept(self):
        # Cribbed from http_server.
        self.total_clients.increment()
        try:
            conn, addr = self.accept()
        except socket.error:
            # linux: on rare occasions we get a bogus socket back from
            # accept.  socketmodule.c:makesockaddr complains that the
            # address family is unknown.  We don't want the whole server
            # to shut down because of this.
            sys.stderr.write ('warning: server accept() threw an exception\n')
            return

        # Turn the vanilla socket into an SSL connection.
        try:
            ssl_conn=SSL.Connection(self.ssl_ctx, conn)
            ssl_conn._setup_ssl(addr)
            ssl_conn.accept_ssl()
            self.channel_class(self, ssl_conn, addr)
        except SSL.SSLError:
            pass

    def writeable(self):
        return 0

