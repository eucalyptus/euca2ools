#!/usr/bin/env python

"""Demo for client-side ssl_dispatcher usage. Note that connect() 
is blocking. (Need fix?) 

This isn't really a HTTPS client; it's just a toy.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

import asyncore, sys, time
from M2Crypto import Rand, SSL

class https_client(SSL.ssl_dispatcher):

    def __init__(self, host, path, ssl_ctx):
        SSL.ssl_dispatcher.__init__(self)
        self.path = path
        self.buffer = 'GET %s HTTP/1.0\r\n\r\n' % self.path
        self.create_socket(ssl_ctx)
        self.socket.connect((host, 19443))
        self._can_read = 1
        self._count = 0

    def handle_connect(self):
        pass

    def readable(self):
        return self._can_read

    def handle_read(self):
        try:
            result = self.recv()
            if result is None:
                return
            elif result == '':
                self._can_read = 0
                sys.stdout.write('%s: total: %5d\n' % (self.path, self._count,))
                sys.stdout.flush()
                self.close()
            else:
                #print result
                l = len(result)
                self._count = self._count + l
                display = (time.time(), l, self.path)
                sys.stdout.write('%14.3f: read %5d from %s\n' % display)
                sys.stdout.flush()
        except SSL.SSLError, why:
            print 'handle_read:', why
            self.close()
            raise

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        try:
            sent = self.send(self.buffer)
            self.buffer = self.buffer[sent:]
        except SSL.SSLError, why:
            print 'handle_write:', why
            self.close()


if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1) 
    ctx = SSL.Context()
    url = ('/jdk118/api/u-names.html', 
        '/postgresql/xfunc-c.html', 
        '/python2.1/modindex.html')
    for u in url:
        https_client('localhost', u, ctx)
    asyncore.loop()
    Rand.save_file('../randpool.dat')


# Here's a sample output. Server is Apache+mod_ssl on localhost.
# $ python https_cli_async.py 
# 991501090.682: read   278 from /python2.1/modindex.html
# 991501090.684: read   278 from /postgresql/xfunc-c.html
# 991501090.742: read  4096 from /postgresql/xfunc-c.html
# 991501090.743: read  4096 from /postgresql/xfunc-c.html
# 991501090.744: read  4096 from /postgresql/xfunc-c.html
# 991501090.744: read  4096 from /postgresql/xfunc-c.html
# 991501090.755: read  4096 from /postgresql/xfunc-c.html
# 991501090.756: read   278 from /jdk118/api/u-names.html
# 991501090.777: read  4096 from /postgresql/xfunc-c.html
# 991501090.778: read  4096 from /postgresql/xfunc-c.html
# 991501090.778: read  4096 from /postgresql/xfunc-c.html
# 991501090.782: read  4096 from /postgresql/xfunc-c.html
# 991501090.813: read  4096 from /python2.1/modindex.html
# 991501090.839: read  4096 from /jdk118/api/u-names.html
# 991501090.849: read  4096 from /python2.1/modindex.html
# 991501090.873: read  3484 from /postgresql/xfunc-c.html
# 991501090.874: read  4096 from /jdk118/api/u-names.html
# 991501090.874: read  4096 from /python2.1/modindex.html
#/postgresql/xfunc-c.html: total: 40626
# 991501090.886: read  4096 from /jdk118/api/u-names.html
# 991501090.886: read  2958 from /python2.1/modindex.html
# 991501090.887: read  4096 from /jdk118/api/u-names.html
#/python2.1/modindex.html: total: 15524
# 991501090.893: read  4096 from /jdk118/api/u-names.html
# 991501090.894: read  2484 from /jdk118/api/u-names.html
#/jdk118/api/u-names.html: total: 23242
# $


