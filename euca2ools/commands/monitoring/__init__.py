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
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.request import AWSQueryRequest
import requestbuilder.service

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from euca2ools.util import strip_response_metadata, add_fake_region_name


class CloudWatch(requestbuilder.service.BaseService):
    NAME = 'monitoring'
    DESCRIPTION = 'Instance monitoring service'
    API_VERSION = '2010-08-01'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    URL_ENVVAR = 'AWS_CLOUDWATCH_URL'

    ARGS = [Arg('-U', '--url', metavar='URL',
                help='instance monitoring service endpoint URL')]

    def configure(self):
        requestbuilder.service.BaseService.configure(self)
        add_fake_region_name(self)

    def handle_http_error(self, response):
        raise AWSError(response)


class CloudWatchRequest(AWSQueryRequest, TabifyingMixin):
    SUITE = Euca2ools
    SERVICE_CLASS = CloudWatch
    AUTH_CLASS = requestbuilder.auth.aws.HmacV4Auth
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = AWSQueryRequest.parse_response(self, response)
        return strip_response_metadata(response_dict)

    def print_alarm(self, alarm):
        bits = [alarm.get('AlarmName')]
        if self.args['show_long']:
            bits.append(alarm.get('AlarmDescription'))
        bits.append(alarm.get('StateValue'))
        if self.args['show_long']:
            bits.append(alarm.get('StateReason'))
            bits.append(alarm.get('StateReasonData'))
            bits.append(alarm.get('ActionsEnabled'))
            bits.append(','.join(alarm.get('OKActions', [])))
        bits.append(','.join(alarm.get('AlarmActions', [])))
        if self.args['show_long']:
            bits.append(','.join(alarm.get('InsufficientDataActions', [])))
        bits.append(alarm.get('Namespace'))
        bits.append(alarm.get('MetricName'))
        if self.args['show_long']:
            dimensions = []
            for dimension in alarm.get('Dimensions', []):
                dimensions.append('{0}={1}'.format(dimension.get('Name'),
                                                   dimension.get('Value')))
            if len(dimensions) > 0:
                bits.append('{{{0}}}'.format(','.join(dimensions)))
            else:
                bits.append(None)
        bits.append(alarm.get('Period'))
        bits.append(alarm.get('Statistic'))
        if self.args['show_long']:
            bits.append(alarm.get('Unit'))
        bits.append(alarm.get('EvaluationPeriods'))
        bits.append(alarm.get('ComparisonOperator'))
        bits.append(alarm.get('Threshold'))
        if self.args['show_long']:
            bits.append(alarm.get('AlarmArn'))
        print self.tabify(bits)
