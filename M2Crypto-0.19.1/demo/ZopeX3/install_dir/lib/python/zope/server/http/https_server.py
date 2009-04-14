##############################################################################
#
# Copyright (c) 2004, Ng Pheng Siong.
# All Rights Reserved.
#
# XXX license TBD; should be Zope 3's ZPL, I just haven't read thru that.
#
##############################################################################
"""HTTPS Server

This is a HTTPS version of HTTPServer.

$Id: https_server.py 240 2004-10-02 12:40:14Z ngps $
"""

import asyncore, logging, os.path

from zope.server.http.httpserver import HTTPServer
from zope.server.http.https_serverchannel import HTTPS_ServerChannel
from M2Crypto import SSL, version


# 2004-09-27, ngps:
# 'sslv2' or 'sslv23' interoperates with Firefox and IE.
# 'sslv3' or 'tlsv1' doesn't.
def make_ssl_context(dir, ssl_proto='sslv23'):
    sslctx = SSL.Context(ssl_proto)
    sslctx.load_cert(os.path.join(dir, 'server.pem'))
    sslctx.load_verify_locations(os.path.join(dir, 'ca.pem'))
    sslctx.load_client_CA(os.path.join(dir, 'ca.pem'))
    sslctx.set_verify(SSL.verify_none, 10)
    sslctx.set_session_id_ctx('someblahblahthing')
    sslctx.set_tmp_dh(os.path.join(dir, 'dh1024.pem'))
    #sslctx.set_info_callback() # debugging only; not thread-safe
    return sslctx


class HTTPS_Server(HTTPServer):
    """This is a generic HTTPS Server."""

    channel_class = HTTPS_ServerChannel
    SERVER_IDENT = 'zope.server.zserverssl_https'

    def __init__(self, ip, port, ssl_ctx=None, task_dispatcher=None, adj=None, start=1,
                 hit_log=None, verbose=0):
        HTTPServer.__init__(self, ip, port, task_dispatcher, adj, start, hit_log, verbose)
        if ssl_ctx is None:
            self.ssl_ctx = make_ssl_context(os.path.realpath(__file__))
        else: 
            self.ssl_ctx = ssl_ctx

    def executeRequest(self, task):
        """Execute an HTTP request."""
        # This is a default implementation, meant to be overridden.
        body = "The HTTPS server is running!\r\n" * 10
        task.response_headers['Content-Type'] = 'text/plain'
        task.response_headers['Content-Length'] = str(len(body))
        task.write(body)

    def handle_accept(self):
        """See zope.server.interfaces.IDispatcherEventHandler"""
        try:
            v = self.accept()
            if v is None:
                return
            conn, addr = v
        except socket.error:
            # Linux: On rare occasions we get a bogus socket back from
            # accept.  socketmodule.c:makesockaddr complains that the
            # address family is unknown.  We don't want the whole server
            # to shut down because of this.
            if self.adj.log_socket_errors:
                self.log_info ('warning: server accept() threw an exception',
                               'warning')
            return
        for (level, optname, value) in self.adj.socket_options:
            conn.setsockopt(level, optname, value)
        # Turn the vanilla socket into an SSL connection.
        try:
            ssl_conn = SSL.Connection(self.ssl_ctx, conn)
            ssl_conn._setup_ssl(addr)
            ssl_conn.accept_ssl()
            self.channel_class(self, ssl_conn, addr, self.adj)
        except SSL.SSLError, why:
            self.log_info('accept: cannot make SSL connection %s' % (why,), 'warning')
            pass



if __name__ == '__main__':

    from zope.server.taskthreads import ThreadedTaskDispatcher
    td = ThreadedTaskDispatcher()
    td.setThreadCount(4)
    HTTPS_Server('', 8443, ssl_ctx=None, task_dispatcher=td, verbose=1)

    try:
        import asyncore
        while 1:
            asyncore.poll(5)

    except KeyboardInterrupt:
        print 'shutting down...'
        td.shutdown()
