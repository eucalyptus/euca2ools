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

import M2Crypto
import base64
import boto.auth_handler
import datetime
import hashlib
import hmac
import time
import urllib
import warnings
from boto.exception import BotoClientError

class EucaRsaAuthV1Handler(boto.auth_handler.AuthHandler):
    """Provides Eucalyptus NC Authentication."""

    capability = ['euca-rsa-v1', 'euca-nc']

    def __init__(self, host, config, provider):
        boto.auth_handler.AuthHandler.__init__(self, host, config, provider)
        self.hmac = hmac.new(provider.secret_key, digestmod=hashlib.sha1)
        self.private_key_path = None

    def _calc_signature(self, params, headers, verb, path):
        boto.log.debug('using euca_signature')
        string_to_sign = '%s\n%s\n%s\n' % (verb, headers['Date'], path)
        keys = params.keys()
        keys.sort()
        pairs = []
        for key in keys:
            val = params[key]
            pairs.append(urllib.quote(key, safe='') + '=' + urllib.quote(val, safe='-_~'))
        qs = '&'.join(pairs)
        boto.log.debug('query string: %s' % qs)
        string_to_sign += qs
        hmac = self.hmac.copy()
        hmac.update(string_to_sign)
        sha_manifest = hashlib.sha1()
        sha_manifest.update(string_to_sign)
        private_key = M2Crypto.RSA.load_key(self.private_key_path)
        signature_value = private_key.sign(sha_manifest.digest())
        b64 = base64.b64encode(signature_value)
        boto.log.debug('len(b64)=%d' % len(b64))
        boto.log.debug('base64 encoded digest: %s' % b64)
        return (qs, b64)

    def add_auth(self, http_request, **kwargs):
        headers = http_request.headers
        params = http_request.params
        qs, signature = self._calc_signature(http_request.params,
                                             http_request.headers,
                                             http_request.method,
                                             http_request.path)
        headers['EucaSignature'] = signature
        boto.log.debug('query_string: %s Signature: %s' % (qs, signature))
        if http_request.method == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            http_request.body = qs
        else:
            http_request.body = ''


class EucaNCAuthHandler(EucaRsaAuthV1Handler):
    # For API compatibility

    def __init__(self, host, config, provider):
        warnings.warn(('EucaNCAuthHandler has been renamed to '
                       'EucaRsaAuthV1Handler'), DeprecationWarning)
        EucaRsaAuthV1Handler.__init__(self, host, config, provider)


class EucaRsaAuthV2Handler(boto.auth_handler.AuthHandler):
    '''Provides authentication for inter-component requests'''

    capability = ['euca-rsa-v2']

    def __init__(self, host, config, provider):
        boto.auth_handler.AuthHandler.__init__(self, host, config, provider)
        self.cert_path        = None
        self.private_key_path = None

    def add_auth(self, http_request, **kwargs):
        if 'Authorization' in http_request.headers:
            del http_request.headers['Authorization']
        now = datetime.datetime.utcnow()
        http_request.headers['Date'] = now.strftime('%Y%m%dT%H%M%SZ')

        cert_fp = self._get_fingerprint()

        headers_to_sign = self._get_headers_to_sign(http_request)
        signed_headers  = self._get_signed_headers(headers_to_sign)
        boto.log.debug('SignedHeaders:%s', signed_headers)

        canonical_request = self._get_canonical_request(http_request)
        boto.log.debug('CanonicalRequest:\n%s', canonical_request)
        signature = self._sign(canonical_request)
        boto.log.debug('Signature:%s', signature)

        auth_header = ' '.join(('EUCA2-RSA-SHA256', cert_fp, signed_headers,
                                signature))
        http_request.headers['Authorization'] = auth_header

    def _get_fingerprint(self):
        cert = M2Crypto.X509.load_cert(self.cert_path)
        return cert.get_fingerprint().lower()

    def _sign(self, canonical_request):
        privkey = M2Crypto.RSA.load_key(self.private_key_path)
        digest  = hashlib.sha256(canonical_request).digest()
        return base64.b64encode(privkey.sign(digest, algo='sha256'))

    def _get_canonical_request(self, http_request):
        # 1.  request method
        method = http_request.method.upper()
        # 2.  CanonicalURI
        c_uri  = self._get_canonical_uri(http_request)
        # 3.  CanonicalQueryString
        c_querystr = self._get_canonical_querystr(http_request)
        # 4.  CanonicalHeaders
        headers_to_sign = self._get_headers_to_sign(http_request)
        c_headers = self._get_canonical_headers(headers_to_sign)
        # 5.  SignedHeaders
        s_headers = self._get_signed_headers(headers_to_sign)

        return '\n'.join((method, c_uri, c_querystr, c_headers, s_headers))

    def _get_canonical_uri(self, http_request):
        return http_request.path or '/'

    def _get_canonical_querystr(self, http_request):
        params = []
        for key, val in http_request.params.iteritems():
            params.append(urllib.quote(param,    safe='/~') + '=' +
                          urllib.quote(str(val), safe='~'))
        return '&'.join(sorted(params))

    def _get_headers_to_sign(self, http_request):
        headers = {'Host': http_request.host}
        for key, val in http_request.headers.iteritems():
            if key.lower() != 'authorization':
                headers[key] = val
        return headers

    def _get_canonical_headers(self, headers):
        header_strs = [key.lower().strip() + ':' + val.strip()
                       for key, val in headers.iteritems()]
        return '\n'.join(sorted(header_strs))

    def _get_signed_headers(self, headers):
        return ';'.join(sorted(header.lower().strip() for header in headers))
