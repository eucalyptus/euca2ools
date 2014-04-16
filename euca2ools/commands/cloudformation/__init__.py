# Copyright 2014 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg
import requestbuilder.auth
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.request import AWSQueryRequest
import requestbuilder.service

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import strip_response_metadata, substitute_euca_region


class CloudFormation(requestbuilder.service.BaseService):
    NAME = 'cloudformation'
    DESCRIPTION = 'Deployment templating service'
    API_VERSION = '2010-05-15'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    URL_ENVVAR = 'AWS_CLOUDFORMATION_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='Deployment templating service endpoint URL')]

    def configure(self):
        substitute_euca_region(self)
        requestbuilder.service.BaseService.configure(self)

    def handle_http_error(self, response):
        raise AWSError(response)


class CloudFormationRequest(AWSQueryRequest, TabifyingMixin):
    SUITE = Euca2ools
    SERVICE_CLASS = CloudFormation
    AUTH_CLASS = requestbuilder.auth.QuerySigV2Auth
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = AWSQueryRequest.parse_response(self, response)
        return strip_response_metadata(response_dict)

    def print_stack(self, stack):
        stack_bits = ['STACK']
        for attr in ('StackName', 'StackStatus', 'StackStatusReason',
                     'Description', 'Outputs', 'CreationTime'):
            stack_bits.append(stack.get(attr))
        print self.tabify(stack_bits)

    def print_stack_event(self, event):
        event_bits = ['EVENT']
        for attr in ('StackName', 'EventId', 'ResourceType',
                     'LogicalResourceId', 'PhysicalResourceId',
                     'Timestamp', 'ResourceStatus', 'ResourceStatusReason'):
            event_bits.append(event.get(attr))
        print self.tabify(event_bits)

    def print_resource(self, resource):
        resource_bits = ['RESOURCE']
        for attr in ('LogicalResourceId', 'PhysicalResourceId', 'ResourceType',
                     'LastUpdatedTimestamp', 'ResourceStatus'):
            resource_bits.append(resource.get(attr))
        print self.tabify(resource_bits)
