# Copyright 2013-2015 Eucalyptus Systems, Inc.
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
import sys

from requestbuilder import Arg
import requestbuilder.auth.aws
import requestbuilder.service
import requestbuilder.request

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import strip_response_metadata


class AutoScaling(requestbuilder.service.BaseService):
    NAME = 'autoscaling'
    DESCRIPTION = 'Auto-scaling service'
    API_VERSION = '2011-01-01'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    URL_ENVVAR = 'AWS_AUTO_SCALING_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='auto-scaling service endpoint URL')]

    def handle_http_error(self, response):
        raise AWSError(response)


class AutoScalingRequest(requestbuilder.request.AWSQueryRequest):
    SUITE = Euca2ools
    SERVICE_CLASS = AutoScaling
    AUTH_CLASS = requestbuilder.auth.aws.HmacV4Auth
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = requestbuilder.request.AWSQueryRequest.parse_response(
            self, response)
        return strip_response_metadata(response_dict)
