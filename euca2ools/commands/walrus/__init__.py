# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from requestbuilder import Arg, MutuallyExclusiveArgList, SERVICE
import requestbuilder.auth
import requestbuilder.request
import requestbuilder.service
from requestbuilder.xmlparse import parse_aws_xml
import string
import urlparse


class Walrus(requestbuilder.service.BaseService):
    NAME = 's3'
    DESCRIPTION = 'Object storage service'
    AUTH_CLASS = requestbuilder.auth.S3RestAuth
    URL_ENVVAR = 'S3_URL'

    ARGS = [MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='REGION',
                    route_to=SERVICE,
                    help='region name to connect to, with optional identity'),
                Arg('-U', '--url', metavar='URL', route_to=SERVICE,
                    help='storage service endpoint URL'))]

    def handle_http_error(self, response):
        raise AWSError(response)


class WalrusRequest(requestbuilder.request.BaseRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = Walrus

    def __init__(self, **kwargs):
        requestbuilder.request.BaseRequest.__init__(self, **kwargs)
        self.redirects_left = 3

    def handle_server_error(self, err):
        if 300 <= err.status_code < 400 and 'Endpoint' in err.elements:
            # When S3 does an inter-region redirect it doesn't supply the new
            # location in the usual header, but rather supplies a new endpoint
            # in the error's XML.  This forces us to handle it manually.
            self.log.debug('-- response content --\n',
                           extra={'append': True})
            self.log.debug(self.response.text, extra={'append': True})
            self.log.debug('-- end of response content --')
            self.log.info('result: redirect')
            if self.redirects_left > 0:
                self.redirects_left -= 1
                parsed = list(urlparse.urlparse(self.service.endpoint))
                parsed[1] = err.elements['Endpoint']
                new_url = urlparse.urlunparse(parsed)
                self.log.debug('redirecting to %s (%i redirects remaining)',
                               new_url, self.redirects_left)
                self.service.endpoint = new_url
                return self.send()
            else:
                self.log.warn('too many redirects; giving up')
        raise


def validate_generic_bucket_name(bucket):
    if len(bucket) == 0:
        raise ValueError('name is too short')
    if len(bucket) > 255:
        raise ValueError('name is too long')
    for char in bucket:
        if char not in string.ascii_letters + string.digits + '.-_':
            raise ValueError('invalid character \'{0}\''.format(char))


def validate_dns_bucket_name(bucket):
    if len(bucket) < 3:
        raise ValueError('name is too short')
    if len(bucket) > 63:
        raise ValueError('name is too long')
    if bucket.startswith('.'):
        raise ValueError('name may not start with \'.\'')
    if bucket.endswith('.'):
        raise ValueError('name may not end with \'.\'')
    labels = bucket.split('.')
    for label in labels:
        if len(label) == 0:
            raise ValueError('name may not contain \'..\'')
        for char in label:
            if char not in string.ascii_lowercase + string.digits + '-':
                raise ValueError('invalid character \'{0}\''.format(char))
        if label[0] not in string.ascii_lowercase + string.digits:
            raise ValueError(('character \'{0}\' may not begin part of a '
                              'bucket name').format(char))
        if label[-1] not in string.ascii_lowercase + string.digits:
            raise ValueError(('character \'{0}\' may not end part of a '
                              'bucket name').format(char))
    if len(labels) == 4:
        try:
            bucket_as_digits = map(int, bucket.split('.'))
        except ValueError:
            # This is actually the case we want
            pass
        else:
            raise ValueError('name must not be formatted like an IP address')
