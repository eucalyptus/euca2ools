##############################################################################
#
# Copyright (c) 2004, Ng Pheng Siong.
# All Rights Reserved.
#
# XXX license TBD; should be Zope 3's ZPL, I just haven't read thru that.
#
##############################################################################
"""HTTPS Server that uses the Zope Publisher for executing a task.

$Id: publisherhttps_server.py 240 2004-10-02 12:40:14Z ngps $
"""
import os.path, sys
from zope.server.http.https_server import HTTPS_Server, make_ssl_context
from zope.publisher.publish import publish


def get_instance_ssldir():
    # This is real cheesy: It seems Zope3 doesn't have convenient
    # programmatic access to INSTANCE_HOME. This code relies on zopectl
    # setting the first entry of PYTHONPATH to $INSTANCE_HOME/lib/python.
    return os.path.join(os.path.dirname(os.path.dirname(sys.path[0])), 'ssl')


class PublisherHTTPS_Server(HTTPS_Server):
    """Zope Publisher-specific HTTPS Server"""

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):

        # The common HTTP
        self.request_factory = request_factory

        # An HTTP server is not limited to serving up HTML; it can be
        # used for other protocols, like XML-RPC, SOAP and so as well
        # Here we just allow the logger to output the sub-protocol type.
        if sub_protocol:
            self.SERVER_IDENT += ' (%s)' %str(sub_protocol)

        kw['ssl_ctx'] = make_ssl_context(get_instance_ssldir())
        HTTPS_Server.__init__(self, *args, **kw)

    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        env['HTTPS'] = 'ON'
        try:
            del env['HTTP']
        except KeyError:
            pass
        instream = task.request_data.getBodyStream()

        request = self.request_factory(instream, task, env)
        response = request.response
        response.setHeaderOutput(task)
        response.setHTTPTransaction(task)
        publish(request)


class PMDBHTTPS_Server(PublisherHTTPS_Server):
    """Enter the post-mortem debugger when there's an error"""

    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        env['HTTPS'] = 'ON'
        try:
            del env['HTTP']
        except KeyError:
            pass
        instream = task.request_data.getBodyStream()

        request = self.request_factory(instream, task, env)
        response = request.response
        response.setHeaderOutput(task)
        try:
            publish(request, handle_errors=False)
        except:
            import sys, pdb
            print "%s:" % sys.exc_info()[0]
            print sys.exc_info()[1]
            pdb.post_mortem(sys.exc_info()[2])
            raise

