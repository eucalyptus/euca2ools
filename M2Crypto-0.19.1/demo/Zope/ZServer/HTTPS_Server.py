##############################################################################
#
# Copyright (c) 2000-2004, Ng Pheng Siong. All Rights Reserved.
# This file is derived from Zope's ZServer/HTTPServer.py.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""
Medusa HTTPS server for Zope

changes from Medusa's http_server:

    Request Threads -- Requests are processed by threads from a thread
    pool.
    
    Output Handling -- Output is pushed directly into the producer
    fifo by the request-handling thread. The HTTP server does not do
    any post-processing such as chunking.

    Pipelineable -- This is needed for protocols such as HTTP/1.1 in
    which mutiple requests come in on the same channel, before
    responses are sent back. When requests are pipelined, the client
    doesn't wait for the response before sending another request. The
    server must ensure that responses are sent back in the same order
    as requests are received.


changes from Zope's HTTP server:

    Well, this is a *HTTPS* server :)

    X.509 certificate-based authentication -- When this is in force,
    zhttps_handler, a subclass of zhttp_handler, is installed.  The
    https server is configured to request an X.509 certificate from
    the client. When the request reaches zhttps_handler, it sets
    REMOTE_USER to the client's subject distinguished name (DN) from
    the certificate. Zope's REMOTE_USER machinery takes care of the
    rest, e.g., in conjunction with the RemoteUserFolder product.
    
""" 

import sys, time, types

from PubCore import handle
from medusa import asyncore
from ZServer import CONNECTION_LIMIT, ZOPE_VERSION
from HTTPServer import zhttp_handler
from zLOG import register_subsystem

from M2Crypto import SSL, version
from medusa.https_server import https_server, https_channel
from medusa.asyncore import dispatcher


ZSERVER_SSL_VERSION=version

register_subsystem('ZServer HTTPS_Server')


class zhttps0_handler(zhttp_handler):
    "zhttps0 handler - sets SSL request headers a la mod_ssl"

    def __init__ (self, module, uri_base=None, env=None):
        zhttp_handler.__init__(self, module, uri_base, env)

    def get_environment(self, request):
        env = zhttp_handler.get_environment(self, request)
        env['SSL_CIPHER'] = request.channel.get_cipher()
        return env


class zhttps_handler(zhttps0_handler):
    "zhttps handler - sets REMOTE_USER to user's X.509 certificate Subject DN"

    def __init__ (self, module, uri_base=None, env=None):
        zhttps0_handler.__init__(self, module, uri_base, env)

    def get_environment(self, request):
        env = zhttps0_handler.get_environment(self, request)
        peer = request.channel.get_peer_cert()
        if peer is not None:
            env['REMOTE_USER'] = str(peer.get_subject())
        return env


class zhttps_channel(https_channel):
    "https channel"

    closed=0
    zombie_timeout=100*60 # 100 minutes
    
    def __init__(self, server, conn, addr):
        https_channel.__init__(self, server, conn, addr)
        self.queue=[]
        self.working=0
        self.peer_found=0
    
    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in 
        # producers by default
        if self.closed:
            return
        self.producer_fifo.push(producer)
        if send: self.initiate_send()
        
    push_with_producer=push

    def work(self):
        "try to handle a request"
        if not self.working:
            if self.queue:
                self.working=1
                try: module_name, request, response=self.queue.pop(0)
                except: return
                handle(module_name, request, response)
        
    def close(self):
        self.closed=1
        while self.queue:
            self.queue.pop()
        if self.current_request is not None:
            self.current_request.channel=None # break circ refs
            self.current_request=None
        while self.producer_fifo:
            p=self.producer_fifo.first()
            if p is not None and type(p) != types.StringType:
                p.more() # free up resources held by producer
            self.producer_fifo.pop()
        self.del_channel()
        #self.socket.set_shutdown(SSL.SSL_SENT_SHUTDOWN|SSL.SSL_RECEIVED_SHUTDOWN)
        self.socket.close()

    def done(self):
        "Called when a publishing request is finished"
        self.working=0
        self.work()

    def kill_zombies(self):
        now = int (time.time())
        for channel in asyncore.socket_map.values():
            if channel.__class__ == self.__class__:
                if (now - channel.creation_time) > channel.zombie_timeout:
                    channel.close()


class zhttps_server(https_server):    
    "https server"
    
    SERVER_IDENT='ZServerSSL/%s' % (ZSERVER_SSL_VERSION,)
    
    channel_class = zhttps_channel
    shutup = 0

    def __init__(self, ip, port, ssl_ctx, resolver=None, logger_object=None):
        self.shutup = 1
        https_server.__init__(self, ip, port, ssl_ctx, resolver, logger_object)
        self.ssl_ctx = ssl_ctx
        self.shutup = 0        
        self.log_info('(%s) HTTPS server started at %s\n'
                      '\tHostname: %s\n\tPort: %d' % (
                        self.SERVER_IDENT,
                        time.ctime(time.time()),
                        self.server_name,
                        self.server_port
                        ))
        
    def log_info(self, message, type='info'):
        if self.shutup: return
        dispatcher.log_info(self, message, type)

    def readable(self):
        return self.accepting and \
                len(asyncore.socket_map) < CONNECTION_LIMIT

    def listen(self, num):
        # override asyncore limits for nt's listen queue size
        self.accepting = 1
        return self.socket.listen (num)

