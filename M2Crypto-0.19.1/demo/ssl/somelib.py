"""
Sample 3rd party lib to use with socklib and myapp.

Copyright (c) 2007 Open Source Applications Foundation.
All rights reserved.
"""
# This represents some 3rd party library we don't want to modify

import socket

class HttpsGetSlash(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def get(self, host, port):
        self.socket.connect((host, port))
        ssl_sock = socket.ssl(self.socket)
        ssl_sock.write('GET / HTTP/1.0\n\n')
        print ssl_sock.read()
        self.socket.close()