"""M2Crypto support for Python 1.5.2 and Python 2.x's httplib. 

Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved."""

import string, sys
from httplib import *
import SSL

if sys.version[0] == '2':
    
    if sys.version[:3] in ['2.1', '2.2']:
        # In 2.1 and above, httplib exports "HTTP" only.
        from httplib import HTTPConnection, HTTPS_PORT
        # ISS Added:
        from httplib import HTTPResponse,FakeSocket

    class HTTPSConnection(HTTPConnection):
    
        """
        This class allows communication via SSL using M2Crypto.
        """
    
        default_port = HTTPS_PORT
    
        def __init__(self, host, port=None, **ssl):
            keys = ssl.keys()
            try: 
                keys.remove('key_file')
            except ValueError:
                pass
            try:
                keys.remove('cert_file')
            except ValueError:
                pass
            try:
                keys.remove('ssl_context')
            except ValueError:
                pass
            if keys:
                raise IllegalKeywordArgument()
            try:
                self.ssl_ctx = ssl['ssl_context']
                assert isinstance(self.ssl_ctx, SSL.Context)
            except KeyError:
                self.ssl_ctx = SSL.Context('sslv23')
            HTTPConnection.__init__(self, host, port)
    
        def connect(self):
            self.sock = SSL.Connection(self.ssl_ctx)
            self.sock.connect((self.host, self.port))
    
        def close(self):
            # This kludges around line 545 of httplib.py,
            # which closes the connection in this object;
            # the connection remains open in the response
            # object.
            #
            # M2Crypto doesn't close-here-keep-open-there,
            # so, in effect, we don't close until the whole 
            # business is over and gc kicks in.
            #
            # Long-running callers beware leakage.
            #
            # 05-Jan-2002: This module works with Python 2.2,
            # but I've not investigated if the above conditions
            # remain.
            pass


    class HTTPS(HTTP):
        
        _connection_class = HTTPSConnection
    
        def __init__(self, host='', port=None, **ssl):
            HTTP.__init__(self, host, port)
            try:
                self.ssl_ctx = ssl['ssl_context']
            except KeyError:
                self.ssl_ctx = SSL.Context('sslv23')


elif sys.version[:3] == '1.5':

    class HTTPS(HTTP):
    
        def __init__(self, ssl_context, host='', port=None):
            assert isinstance(ssl_context, SSL.Context)
            self.debuglevel=0
            self.file=None
            self.ssl_ctx=ssl_context
            if host:
                self.connect(host, port)
    
        def connect(self, host, port=None):
            # Cribbed from httplib.HTTP.
            if not port:
                i = string.find(host, ':')
                if i >= 0:
                    host, port = host[:i], host[i+1:]
                    try: port = string.atoi(port)
                    except string.atoi_error:
                        raise socket.error, "nonnumeric port"
            if not port: port = HTTPS_PORT
            self.sock = SSL.Connection(self.ssl_ctx)
            if self.debuglevel > 0: print 'connect:', (host, port)
            self.sock.connect((host, port))

# ISS Added.
# From here, starts the proxy patch
class HTTPProxyConnection(HTTPConnection):
    """
    This class provides HTTP access through (authenticated) proxies.
    
    Example:
    If the HTTP proxy address is proxy.your.org:8080, an authenticated proxy
    (one which requires a username/password combination in order to serve
    requests), one can fetch HTTP documents from 'www.webserver.net', port 81:

    conn = HTTPProxyConnection('proxy.your.org:8080', 'www.webserver.net',
        port=81, username='username', password='password')
    conn.connect()
    conn.request("HEAD", "/index.html", headers={'X-Custom-Header-1' : 'Value-1'})
    resp = conn.getresponse()
    ...

    """
    def __init__(self, proxy, host, port=None, username=None, password=None):
        # The connection goes through the proxy
        HTTPConnection.__init__(self, proxy)
        # save the proxy connection settings
        self.__proxy, self.__proxy_port = self.host, self.port
        # self.host and self.port will point to the real host
        self._set_hostport(host, port)
        # save the host and port
        self._host, self._port = self.host, self.port
        # Authenticated proxies support
        self.__username = username
        self.__password = password

    def connect(self):
        """Connect to the host and port specified in __init__ (through a
        proxy)."""
        # We are connecting to the proxy, so use the proxy settings
        self._set_hostport(self.__proxy, self.__proxy_port)
        HTTPConnection.connect(self)
        # Restore the real host and port
        self._set_hostport(self._host, self._port)

    def putrequest(self, method, url):
        """Send a request to the server.

        `method' specifies an HTTP request method, e.g. 'GET'.
        `url' specifies the object being requested, e.g. '/index.html'.
        """
        # The URL has to include the real host
        hostname = self._host
        if self._port != self.default_port:
            hostname = hostname + ':' + str(self._port)
        newurl = "http://%s%s" % (hostname, url)
        # Piggyback on the parent class
        HTTPConnection.putrequest(self, method, newurl)
        # Add proxy-specific headers
        self._add_auth_proxy_header()
        
    def _add_auth_proxy_header(self):
        """Adds an HTTP header for authenticated proxies
        """
        if not self.__username:
            # No username, so assume not an authenticated proxy
            return
        # Authenticated proxy
        import base64
        userpass = "%s:%s" % (self.__username, self.__password)
        enc_userpass = string.strip(base64.encodestring(userpass))
        self.putheader("Proxy-Authorization", "Basic %s" % enc_userpass)

class HTTPSProxyResponse(HTTPResponse):
    """
    Replacement class for HTTPResponse
    Proxy responses (made through SSL) have to keep the connection open 
    after the initial request, since the connection is tunneled to the SSL
    host with the CONNECT method.
    """
    def begin(self):
        HTTPResponse.begin(self)
        self.will_close = 0

class HTTPSProxyConnection(HTTPProxyConnection):
    """This class provides HTTP access through (authenticated) proxies.
    
    Example:
    If the HTTP proxy address is proxy.your.org:8080, an authenticated proxy
    (one which requires a username/password combination in order to serve
    requests), one can fetch HTTP documents from 'www.webserver.net', port 81:

    conn = HTTPProxyConnection('proxy.your.org:8080', 'www.webserver.net',
        port=81, username='username', password='password')
    conn.connect()
    conn.request("HEAD", "/index.html", headers={'X-Custom-Header-1' : 'Value-1'})
    resp = conn.getresponse()
    ...

    To avoid dealing with multiple inheritance, this class only inherits from
    HTTPProxyConnection.
    """
    default_port = HTTPSConnection.default_port

    def __init__(self, proxy, host, port=None, username=None, password=None, **x509):
        for key in x509.keys():
           if key not in ['cert_file', 'key_file','ssl_context']:
                raise IllegalKeywordArgument()
        self.key_file = x509.get('key_file')
        self.cert_file = x509.get('cert_file')
        #ISS Added
        self.ssl_ctx = x509.get('ssl_context')
        # Piggybacking on HTTPProxyConnection
        HTTPProxyConnection.__init__(self, proxy, host, port, username, password)

    def connect(self):
        """Connect (using SSL) to the host and port specified in __init__ 
        (through a proxy)."""
        import socket
        # Set the connection with the proxy
        HTTPProxyConnection.connect(self)
        # Use the stock HTTPConnection putrequest 
        host = "%s:%s" % (self._host, self._port)
        HTTPConnection.putrequest(self, "CONNECT", host)
        # Add proxy-specific stuff
        self._add_auth_proxy_header()
        # And send the request
        HTTPConnection.endheaders(self)
        # Save the response class
        response_class = self.response_class
        # And replace the response class with our own one, which does not
        # close the connection
        self.response_class = HTTPSProxyResponse
        response = HTTPConnection.getresponse(self)
        # Restore the response class
        self.response_class = response_class
        # Close the response object manually
        response.close()
        if response.status != 200:
            # Close the connection manually
            self.close()
            # XXX Find the appropriate error code
            raise socket.error(1001, response.status, response.value)

        # NgPS: I haven't read the code recently, but I think it is
        # reasonable to assume that self.sock is a connected TCP socket at
        # this point.

        # Use the real stuff. ;-)
        if self.ssl_ctx and isinstance(self.ssl_ctx, SSL.Context):
           self.sock =  SSL.Connection(self.ssl_ctx)
           self.sock.connect((self.host, self.port))
        else:
           # Fake the socket
           ssl = socket.ssl(self.sock, self.key_file, self.cert_file)
           self.sock = FakeSocket(self.sock, ssl)
        if self.debuglevel > 0: print 'socket type:', self.sock

    def putrequest(self, method, url):
        """Send a request to the server.

        `method' specifies an HTTP request method, e.g. 'GET'.
        `url' specifies the object being requested, e.g. '/index.html'.
        """
        # bypass the parent class's putrequest: use the grandparent's one :-)
        return HTTPConnection.putrequest(self, method, url)
