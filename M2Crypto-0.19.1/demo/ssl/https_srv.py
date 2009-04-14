"""This server extends BaseHTTPServer and SimpleHTTPServer thusly:
1. One thread per connection.
2. Generates directory listings. 

In addition, it has the following properties:
1. Works over HTTPS only.
2. Displays SSL handshaking and SSL session info.
3. Performs SSL renegotiation when a magic url is requested.

TODO:
1. Cache stat() of directory entries.
2. Fancy directory indexing.
3. Interface ZPublisher.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved.
"""

import os, sys
from SimpleHTTPServer import SimpleHTTPRequestHandler

from M2Crypto import Rand, SSL
from M2Crypto.SSL.SSLServer import ThreadingSSLServer

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def mkdirlist(path, url):
    dirlist = os.listdir(path)
    dirlist.sort()
    f = StringIO()
    f.write('<title>Index listing for %s</title>\r\n' % (url,))
    f.write('<h1>Index listing for %s</h1>\r\n' % (url,))
    f.write('<pre>\r\n')
    for d in dirlist:
        if os.path.isdir(os.path.join(path, d)):
            d2 = d + '/'
        else:
            d2 = d
        if url == '/':
            f.write('<a href="/%s">%s</a><br>\r\n' % (d, d2))
        else:
            f.write('<a href="%s/%s">%s</a><br>\r\n' % (url, d, d2))
    f.write('</pre>\r\n\r\n')
    f.reset()
    return f


class HTTP_Handler(SimpleHTTPRequestHandler):

    server_version = "https_srv/0.1"
    reneg = 0

    # Cribbed from SimpleHTTPRequestHander to add the ".der" entry,
    # which facilitates installing your own certificates into browsers.
    extensions_map = {
            '': 'text/plain',   # Default, *must* be present
            '.html': 'text/html',
            '.htm': 'text/html',
            '.gif': 'image/gif',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.der': 'application/x-x509-ca-cert'
            }

    def send_head(self):
        if self.path[1:8] == '_reneg_':
            self.reneg = 1
            self.path = self.path[8:]
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            f = mkdirlist(path, self.path)
            filetype = 'text/html'
        else:
            try:
                f = open(path, 'rb')
                filetype = self.guess_type(path)
            except IOError:
                self.send_error(404, "File not found")
                return None
        self.send_response(200)
        self.send_header("Content-type", filetype)
        self.end_headers()
        return f

    def do_GET(self):
        #sess = self.request.get_session()
        #self.log_message('\n%s', sess.as_text())
        f = self.send_head()
        if self.reneg:
            self.reneg = 0
            self.request.renegotiate()
            sess = self.request.get_session()
            self.log_message('\n%s', sess.as_text())
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        #sess = self.request.get_session()
        #self.log_message('\n%s', sess.as_text())
        f = self.send_head()
        if f:
            f.close()


class HTTPS_Server(ThreadingSSLServer):
    def __init__(self, server_addr, handler, ssl_ctx):
        ThreadingSSLServer.__init__(self, server_addr, handler, ssl_ctx)
        self.server_name = server_addr[0]
        self.server_port = server_addr[1]

    def finish(self):
        self.request.set_shutdown(SSL.SSL_RECEIVED_SHUTDOWN | SSL.SSL_SENT_SHUTDOWN)
        self.request.close()


def init_context(protocol, certfile, cafile, verify, verify_depth=10):
    ctx=SSL.Context(protocol)
    ctx.load_cert(certfile)
    ctx.load_client_ca(cafile)
    ctx.load_verify_info(cafile)
    ctx.set_verify(verify, verify_depth)
    ctx.set_allow_unknown_ca(1)
    ctx.set_session_id_ctx('https_srv')
    ctx.set_info_callback()
    return ctx


if __name__ == '__main__':
    from M2Crypto import threading as m2threading
    m2threading.init()
    if len(sys.argv) < 2:
        wdir = '.'
    else:
        wdir = sys.argv[1]
    Rand.load_file('../randpool.dat', -1)
    ctx = init_context('sslv23', 'server.pem', 'ca.pem', \
        SSL.verify_none)
        #SSL.verify_peer | SSL.verify_fail_if_no_peer_cert)
    ctx.set_tmp_dh('dh1024.pem')
    os.chdir(wdir)
    httpsd = HTTPS_Server(('', 19443), HTTP_Handler, ctx)
    httpsd.serve_forever()
    Rand.save_file('../randpool.dat')
    m2threading.cleanup()


