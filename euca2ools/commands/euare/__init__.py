# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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

import argparse
from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from requestbuilder import Arg, MutuallyExclusiveArgList, SERVICE
import requestbuilder.auth
import requestbuilder.request
import requestbuilder.service
import sys


class Euare(requestbuilder.service.BaseService):
    NAME = 'iam'
    DESCRIPTION = 'Eucalyptus User, Authorization and Reporting Environment'
    API_VERSION = '2010-05-08'
    AUTH_CLASS = requestbuilder.auth.QuerySigV2Auth
    URL_ENVVAR = 'EUARE_URL'

    ARGS = [MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='REGION',
                    route_to=SERVICE,
                    help='region name to connect to, with optional identity'),
                Arg('-U', '--url', metavar='URL', route_to=SERVICE,
                    help='storage service endpoint URL'))]

    def handle_http_error(self, response):
        raise AWSError(response)


class EuareRequest(requestbuilder.request.AWSQueryRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = Euare
    METHOD = 'POST'

    def configure(self):
        requestbuilder.request.AWSQueryRequest.configure(self)
        if self.args.get('deprecated_delegate'):
            # Use it and complain
            self.args['DelegateAccount'] = self.args['deprecated_delegate']
            msg = 'argument --delegate is deprecated; use --as-account instead'
            self.log.warn(msg)
            print >> sys.stderr, 'warning:', msg

    def parse_response(self, response):
        response_dict = requestbuilder.request.AWSQueryRequest.parse_response(
            self, response)
        # EUARE responses enclose their useful data inside FooResponse
        # elements.  If that's all we have after stripping out ResponseMetadata
        # then just return its contents.
        useful_keys = list(filter(lambda x: x != 'ResponseMetadata',
                                  response_dict.keys()))
        if len(useful_keys) == 1:
            return response_dict[useful_keys[0]]
        else:
            return response_dict

AS_ACCOUNT = [Arg('--as-account', dest='DelegateAccount', metavar='ACCOUNT',
                  help='''[Eucalyptus only] run this command as the
                          administrator of another account (only usable by
                          cloud administrators)'''),
              Arg('--delegate', dest='deprecated_delegate', route_to=None,
                  help=argparse.SUPPRESS)]
