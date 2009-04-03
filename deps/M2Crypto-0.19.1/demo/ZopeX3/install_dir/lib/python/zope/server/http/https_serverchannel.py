##############################################################################
#
# Copyright (c) 2004, Ng Pheng Siong.
# All Rights Reserved.
#
# XXX license TBD; should be Zope 3's ZPL, I just haven't read thru that.
#
##############################################################################
"""HTTPS Server Channel

$Id: https_serverchannel.py 240 2004-10-02 12:40:14Z ngps $
"""
from zope.server.serverchannelbase import ServerChannelBase
from zope.server.http.httptask import HTTPTask
from zope.server.http.httprequestparser import HTTPRequestParser
from zope.server.http.httpserverchannel import HTTPServerChannel
from M2Crypto import SSL


class HTTPS_ServerChannel(HTTPServerChannel):
    """HTTPS-specific Server Channel"""

    task_class = HTTPTask
    parser_class = HTTPRequestParser

    def send(self, data):
        try:
            result = self.socket._write_nbio(data)
            if result <= 0:
                return 0
            else:
                #self.server.bytes_out.increment(result)
                return result
        except SSL.SSLError, why:
            self.close()
            self.log_info('send: closing channel %s %s' % (repr(self), why), 'warning')
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
                #self.server.bytes_in.increment(len(result))
                return result
        except SSL.SSLError, why:
            self.close()
            self.log_info('recv: closing channel %s %s' % (repr(self), why), 'warning')
            return ''


