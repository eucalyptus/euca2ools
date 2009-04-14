##############################################################################
#
# Copyright (c) 2004, Ng Pheng Siong.
# All Rights Reserved.
#
# XXX license TBD; should be Zope 3's ZPL, I just haven't read thru that.
#
##############################################################################
"""HTTPS server factories

$Id: https.py 240 2004-10-02 12:40:14Z ngps $
"""

from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.server.servertype import ServerType
from zope.server.http.commonaccesslogger import CommonAccessLogger
from zope.server.http.publisherhttps_server import PMDBHTTPS_Server
from zope.server.http.publisherhttps_server import PublisherHTTPS_Server

https = ServerType(PublisherHTTPS_Server,
                  HTTPPublicationRequestFactory,
                  CommonAccessLogger,
                  8443, True)

pmhttps = ServerType(PMDBHTTPS_Server,
                    HTTPPublicationRequestFactory,
                    CommonAccessLogger,
                    8376, True)
