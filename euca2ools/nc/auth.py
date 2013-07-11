# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import base64
import datetime
import hashlib
import os.path
from requestbuilder import Arg
from requestbuilder.auth import BaseAuth
from requestbuilder.exceptions import ArgumentError
import subprocess
import urlparse
import urllib


class EucaRsaV2Auth(BaseAuth):
    """Provides authentication for inter-component requests"""

    ARGS = [Arg('--cert', metavar='FILE', help='''file containing the X.509
                certificate to use when signing requests'''),
            Arg('--privatekey', metavar='FILE',
                help='file containing the private key to sign requests with'),
            Arg('--spoof-key-id', metavar='KEY_ID',
                help='run this command as if signed by a specific access key'),
            Arg('--euca-auth', action='store_true', help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        BaseAuth.configure(self)
        if not self.args.get('spoof_key_id'):
            self.args['spoof_key_id'] = os.getenv('EC2_ACCESS_KEY')

        cert = self.args.get('cert') or os.getenv('EUCA_CERT')
        privkey = self.args.get('privatekey') or os.getenv('EUCA_PRIVATE_KEY')
        if not cert:
            raise ArgumentError('argument --cert or environment variable '
                                'EUCA_CERT is required')
        if not privkey:
            raise ArgumentError('argument --privatekey or environment '
                                'variable EUCA_PRIVATE_KEY is required')
        cert = os.path.expanduser(os.path.expandvars(cert))
        privkey = os.path.expanduser(os.path.expandvars(privkey))
        if not os.path.exists(cert):
            raise ArgumentError("certificate file '{0}' does not exist"
                                .format(cert))
        if not os.path.isfile(cert):
            raise ArgumentError("certificate file '{0}' is not a file"
                                .format(cert))
        if not os.path.exists(privkey):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(privkey))
        if not os.path.isfile(privkey):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(privkey))
        self.args['cert'] = cert
        self.args['privatekey'] = privkey

    def __call__(self, request):
        if request.headers is None:
            request.headers = {}
        now = datetime.datetime.utcnow()
        request.headers['Date'] = now.strftime('%Y%m%dT%H%M%SZ')
        if 'Authorization' in request.headers:
            del request.headers['Authorization']
        if self.args.get('spoof_key_id'):
            request.headers['AWSAccessKeyId'] = self.args['spoof_key_id']
        elif 'AWSAccessKeyId' in request.headers:
            del request.headers['AWSAccessKeyId']

        cert_fp = self._get_fingerprint()
        self.log.debug('certificate fingerprint: %s', cert_fp)

        headers_to_sign = self._get_headers_to_sign(request)
        signed_headers = self._get_signed_headers(headers_to_sign)
        self.log.debug('SignedHeaders:%s', signed_headers)

        canonical_request = self._get_canonical_request(request)
        self.log.debug('CanonicalRequest:\n%s', canonical_request)
        signature = self._sign(canonical_request)
        self.log.debug('Signature:%s', signature)

        auth_header = ' '.join(('EUCA2-RSA-SHA256', cert_fp, signed_headers,
                                signature))
        request.headers['Authorization'] = auth_header

    def _get_fingerprint(self):
        cmd = ['openssl', 'x509', '-noout', '-in', self.args['cert'],
               '-fingerprint', '-md5']
        openssl = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (stdout, __) = openssl.communicate()
        if openssl.returncode != 0:
            raise subprocess.CalledProcessError(openssl.returncode, cmd)
        return stdout.strip().rsplit('=', 1)[-1].replace(':', '').lower()

    def _sign(self, canonical_request):
        digest = hashlib.sha256(canonical_request).digest()
        cmd = ['openssl', 'pkeyutl', '-sign', '-inkey',
               self.args['privatekey'], '-pkeyopt', 'digest:sha256']
        openssl = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        (stdout, __) = openssl.communicate(digest)
        if openssl.returncode != 0:
            raise subprocess.CalledProcessError(openssl.returncode, cmd)
        return base64.b64encode(stdout)

    def _get_canonical_request(self, request):
        # 1.  request method
        method = request.method.upper()
        # 2.  CanonicalURI
        c_uri = self._get_canonical_uri(request)
        # 3.  CanonicalQueryString
        c_querystr = self._get_canonical_querystr(request)
        # 4.  CanonicalHeaders
        headers_to_sign = self._get_headers_to_sign(request)
        c_headers = self._get_canonical_headers(headers_to_sign)
        # 5.  SignedHeaders
        s_headers = self._get_signed_headers(headers_to_sign)

        return '\n'.join((method, c_uri, c_querystr, c_headers, s_headers))

    def _get_canonical_uri(self, request):
        return urlparse.urlparse(request.url).path or '/'

    def _get_canonical_querystr(self, request):
        params = []
        for key, val in request.params.iteritems():
            params.append('='.join((urllib.quote(key, safe='/~'),
                                    urllib.quote(str(val), safe='~'))))
        return '&'.join(sorted(params))

    def _get_headers_to_sign(self, request):
        headers = {'Host': urlparse.urlparse(request.url).netloc}
        for key, val in request.headers.iteritems():
            if key.lower() != 'authorization':
                headers[key] = val
        return headers

    def _get_canonical_headers(self, headers):
        header_strs = [str(key).lower().strip() + ':' + str(val).strip()
                       for key, val in headers.iteritems()]
        return '\n'.join(sorted(header_strs))

    def _get_signed_headers(self, headers):
        return ';'.join(sorted(header.lower().strip() for header in headers))
