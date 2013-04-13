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
import requestbuilder.service
import requestbuilder.request


class ELB(requestbuilder.service.BaseService):
    NAME = 'elasticloadbalancing'
    DESCRIPTION = 'Load balancing service'
    API_VERSION = '2012-06-01'
    AUTH_CLASS = requestbuilder.auth.QuerySigV2Auth
    REGION_ENVVAR = 'EUCA_REGION'
    URL_ENVVAR = 'AWS_ELB_URL'

    ARGS = [MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='USER@REGION',
                    route_to=SERVICE, help='''name of the region and/or user
                    in config files to use to connect to the service'''),
                Arg('-U', '--url', metavar='URL', route_to=SERVICE,
                    help='load balancing service endpoint URL'))]

    def handle_http_error(self, response):
        raise AWSError(response)


class ELBRequest(requestbuilder.request.AWSQueryRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = ELB
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = requestbuilder.request.AWSQueryRequest.parse_response(
            self, response)
        useful_keys = list(filter(lambda x: x != 'ResponseMetadata',
                                  response_dict.keys()))
        if len(useful_keys) == 1:
            return response_dict[useful_keys[0]]
        else:
            return response_dict
