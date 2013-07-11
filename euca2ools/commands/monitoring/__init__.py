# Copyright 2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands import Euca2ools
from euca2ools.exceptions import AWSError
from requestbuilder import Arg, MutuallyExclusiveArgList
import requestbuilder.auth
from requestbuilder.mixins import TabifyingMixin
import requestbuilder.service
from requestbuilder.request import AWSQueryRequest


class CloudWatch(requestbuilder.service.BaseService):
    NAME = 'monitoring'
    DESCRIPTION = 'Instance monitoring service'
    API_VERSION = '2010-08-01'
    AUTH_CLASS = requestbuilder.auth.QuerySigV2Auth
    REGION_ENVVAR = 'EUCA_REGION'
    URL_ENVVAR = 'AWS_CLOUDWATCH_URL'

    ARGS = [MutuallyExclusiveArgList(
                Arg('--region', dest='userregion', metavar='USER@REGION',
                    help='''name of the region and/or user in config files to
                    use to connect to the service'''),
                Arg('-U', '--url', metavar='URL',
                    help='instance monitoring service endpoint URL'))]

    def handle_http_error(self, response):
        raise AWSError(response)


class CloudWatchRequest(AWSQueryRequest, TabifyingMixin):
    SUITE = Euca2ools
    SERVICE_CLASS = CloudWatch
    METHOD = 'POST'

    def parse_response(self, response):
        response_dict = AWSQueryRequest.parse_response(self, response)
        useful_keys = list(filter(lambda x: x != 'ResponseMetadata',
                                  response_dict.keys()))
        if len(useful_keys) == 1:
            return response_dict[useful_keys[0]] or {}
        else:
            return response_dict

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
        print self.tabify(bits)
