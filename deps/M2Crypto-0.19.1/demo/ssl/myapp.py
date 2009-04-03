"""
Sample application for socklib and somelib.

Copyright (c) 2007 Open Source Applications Foundation.
All rights reserved.
"""

# Sample application that uses socklib to override socket.ssl in order
# to make the 3rd party library use M2Crypto for SSL, instead of python
# stdlib SSL.

import socklib # sets M2Crypto.SSL.Connection as socket.ssl

# Set up the secure context for socklib
from M2Crypto import SSL

def getContext():
    ctx = SSL.Context()
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
    ctx.load_verify_locations('ca.pem')
    return ctx

socklib.setSSLContextFactory(getContext)

# Import and use 3rd party lib
import somelib

if __name__ == '__main__':
    c = somelib.HttpsGetSlash()
    c.get('verisign.com', 443)
