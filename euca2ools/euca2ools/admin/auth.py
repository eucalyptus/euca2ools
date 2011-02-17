# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Mitch Garnaat mgarnaat@eucalyptus.com

import urllib, base64
import time
import boto.auth_handler
from boto.exception import BotoClientError
from hashlib import sha1 as sha
from M2Crypto import RSA
        
class EucaAdminAuthHandler(boto.auth_handler.AuthHandler):
    """Provides Eucalyptus Admin Authentication."""

    capability = ['euca-admin']

    def _calc_signature(self, params, headers, verb, path):
        boto.log.debug('using calc_signature')
        string_to_sign = '%s\n%s\n%s\n' % (verb, headers['Date'],
                                           self.get_path(path))
        keys = params.keys()
        keys.sort()
        pairs = []
        for key in keys:
            val = self.get_utf8_value(params[key])
            pairs.append(urllib.quote(key, safe='') + '=' + urllib.quote(val, safe='-_~'))
        qs = '&'.join(pairs)
        boto.log.debug('query string: %s' % qs)
        string_to_sign += qs
        hmac = self.hmac.copy()
        hmac.update(string_to_sign)
        sha_manifest = sha()
        sha_manifest.update(string_to_sign)
        private_key = RSA.load_key(self.private_key_path) 
        signature_value = private_key.sign(sha_manifest.digest())
        b64 = base64.b64encode(signature_value)
        boto.log.debug('len(b64)=%d' % len(b64))
        boto.log.debug('base64 encoded digest: %s' % b64)
        return (path, b64)

    def add_auth(self, http_request, **kwargs):
        headers = http_request.headers
        params = http_request.params
        params['AWSAccessKeyId'] = kwargs.get('euid', None)
        cert_path = kwargs.get('cert_path')
        cert_file = open(cert_path, 'r')
        cert_str = cert_file.read()
        cert_file.close()
        headers['EucaCert'] = base64.b64encode(cert_str)
        if not headers.has_key('Content-Length'):
            headers['Content-Length'] = str(len(data))

        if not headers.has_key('Date'):
            headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                            time.gmtime())
        path_base = '/'
        path_base += "%s/" % kwargs.get('bucket')
        path = path_base + urllib.quote(key)
        http_request.path = self.get_path(path)
        qs, signature = self._calc_signature(http_request.params,
                                             http_request.headers,
                                             http_request.method,
                                             http_request.path)
	headers['EucaSignature'] = signature
        boto.log.debug('query_string: %s Signature: %s' % (qs, signature))
        if http_request.method == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            http_request.body = qs + '&Signature=' + urllib.quote(signature)
        else:
            http_request.body = ''
            http_request.path = (http_request.path + '?' + qs + '&Signature=' + urllib.quote(signature))
        # Now that query params are part of the path, clear the 'params' field
        # in request.
        http_request.params = {}

