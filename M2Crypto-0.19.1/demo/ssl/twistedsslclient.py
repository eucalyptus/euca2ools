#!/usr/bin/env python
"""
Demonstrates M2Crypto.SSL.TwistedProtocolWrapper

Copyright (c) 2005 Open Source Applications Foundation. All rights reserved.
"""

import twisted.internet.protocol as protocol
import twisted.protocols.basic as basic
import twisted.internet.reactor as reactor
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL as SSL
        
class EchoClient(basic.LineReceiver):
    def connectionMade(self):
        self.sendLine('Hello World!')

    def lineReceived(self, line):
        print 'received: "%s"' % line
        self.transport.loseConnection()
        

class EchoClientFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed'
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost'
        reactor.stop()


class ContextFactory:
    def getContext(self):
        return SSL.Context()


if __name__ == '__main__':
    factory = EchoClientFactory()
    wrapper.connectSSL('localhost', 8000, factory, ContextFactory())
    reactor.run() # This will block until reactor.stop() is called
