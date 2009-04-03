#!/usr/bin/env python
"""
Demonstrates M2Crypto.SSL.TwistedProtocolWrapper

Copyright (c) 2005 Open Source Applications Foundation. All rights reserved.
"""

import sys
import M2Crypto.SSL as SSL
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import twisted.internet.protocol as protocol
import twisted.internet.reactor as reactor
import twisted.python.log as log


class Echo(protocol.Protocol):
    def dataReceived(self, data):
        print 'received: "%s"' % data
        self.transport.write(data)

    def connectionMade(self):
        print 'connection made'


class ContextFactory:
    def getContext(self):
        ctx = SSL.Context()
        ctx.load_cert('server.pem')
        return ctx


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = protocol.Factory()
    factory.protocol = Echo
    wrapper.listenSSL(8000, factory, ContextFactory())
    reactor.run()
