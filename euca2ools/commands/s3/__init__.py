# Copyright 2013-2014 Eucalyptus Systems, Inc.
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

import os
import string
import sys
import urlparse

from requestbuilder import Arg
import requestbuilder.auth
import requestbuilder.exceptions
import requestbuilder.request
import requestbuilder.service
import requests
import six

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import magic, substitute_euca_region


class S3(requestbuilder.service.BaseService):
    NAME = 's3'
    DESCRIPTION = 'Object storage service'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    URL_ENVVAR = 'S3_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='object storage service endpoint URL')]

    def configure(self):
        substitute_euca_region(self)
        requestbuilder.service.BaseService.configure(self)

    def handle_http_error(self, response):
        raise AWSError(response)

    def build_presigned_url(self, method='GET', path=None, params=None,
                            auth=None, auth_args=None):
        if path:
            # We can't simply use urljoin because a path might start with '/'
            # like it could for keys that start with that character.
            if self.endpoint.endswith('/'):
                url = self.endpoint + path
            else:
                url = self.endpoint + '/' + path
        else:
            url = self.endpoint
        request = requests.Request(method=method, url=url, params=params)
        if auth is not None:
            auth.apply_to_request_params(request, self, **(auth_args or {}))
        p_request = request.prepare()
        return p_request.url

    def resolve_url_to_location(self, url):
        """
        Given a URL, try to return its associated region, bucket, and
        key names based on this object's endpoint info as well as all
        S3 endpoints given in the configuration.
        """
        parsed_url = six.moves.urllib_parse.urlparse(url)
        if not parsed_url.scheme:
            parsed_url = six.moves.urllib_parse.urlparse('http://' + url)
        parsed_own_url = six.moves.urllib_parse.urlparse(self.endpoint)
        bucket, key = self.__match_path(parsed_url, parsed_own_url)
        if bucket:
            return self.region_name, bucket, key
        else:
            # Try to look it up in the config
            s3_urls = self.config.get_all_region_options('s3-url')
            for section, conf_url in s3_urls.iteritems():
                parsed_conf_url = six.moves.urllib_parse.urlparse(conf_url)
                bucket, key = self.__match_path(parsed_url, parsed_conf_url)
                if bucket:
                    region = self.config.get_region_option('name',
                                                           region=section)
                    return region or section, bucket, key
        raise ValueError("URL '{0}' matches no known object storage "
                         "endpoints.  Supply one via the command line or "
                         "configuration.".format(url))

    def __match_path(self, given, service):
        if given.netloc == service.netloc:
            # path-style
            service_path = service.path
            if not service_path.endswith('/'):
                service_path += '/'
            cpath = given.path.split(service_path, 1)[1]
            bucket, key = cpath.split('/', 1)
            self.log.debug('URL path match:  %s://%s%s + %s://%s%s -> %s/%s',
                           given.scheme, given.netloc, given.path,
                           service.scheme, service.netloc, service.path,
                           bucket, key)
        elif given.netloc.endswith(service.netloc):
            # vhost-style
            bucket = given.netloc.rsplit('.' + service.netloc, 1)[0]
            bucket = bucket.lstrip('/')
            if given.path.startswith('/'):
                key = given.path[1:]
            else:
                key = given.path
            self.log.debug('URL vhost match:  %s://%s%s + %s://%s%s -> %s/%s',
                           given.scheme, given.netloc, given.path,
                           service.scheme, service.netloc, service.path,
                           bucket, key)
        else:
            bucket = None
            key = None
        return bucket, key


class S3Request(requestbuilder.request.BaseRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = S3
    AUTH_CLASS = requestbuilder.auth.S3RestAuth

    def __init__(self, **kwargs):
        requestbuilder.request.BaseRequest.__init__(self, **kwargs)
        self.redirects_left = 3

    def get_presigned_url(self, expiration_datetime):
        self.preprocess()
        return self.service.build_presigned_url(
            method=self.method, path=self.path, params=self.params,
            auth=self.auth,
            auth_args={'expiration_datetime': expiration_datetime})

    def handle_server_error(self, err):
        if err.status_code == 301:
            self.log.debug('-- response content --\n',
                           extra={'append': True})
            self.log.debug(self.response.text, extra={'append': True})
            self.log.debug('-- end of response content --')
            self.log.error('result: inter-region redirect')
            msg = 'Aborting due to inter-region redirect'
            if 'Endpoint' in err.elements:
                msg += ' to {0}'.format(err.elements['Endpoint'])
            self.log.debug(msg, exc_info=True)

            if 'Bucket' in err.elements:
                bucket = '"{0}" '.format(err.elements['Bucket'])
            else:
                bucket = ''
            parsed = six.moves.urllib_parse.urlparse(self.service.endpoint)
            msg = ('Bucket {0}is not available from endpoint "{1}".  Ensure '
                   "the object storage service URL matches the bucket's "
                   'location.'.format(bucket, parsed.netloc))
            msg = magic(self.config, 'Your princess is in another castle!',
                        '  ') + msg
            raise requestbuilder.exceptions.ClientError(msg)
        else:
            return requestbuilder.request.BaseRequest.handle_server_error(
                self, err)


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
                              'bucket name').format(label[0]))
        if label[-1] not in string.ascii_lowercase + string.digits:
            raise ValueError(('character \'{0}\' may not end part of a '
                              'bucket name').format(label[-1]))
    if len(labels) == 4:
        try:
            [int(chunk) for chunk in bucket.split('.')]
        except ValueError:
            # This is actually the case we want
            pass
        else:
            raise ValueError('name must not be formatted like an IP address')
