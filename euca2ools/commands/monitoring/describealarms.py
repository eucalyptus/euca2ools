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

import argparse
from euca2ools.commands.monitoring import CloudWatchRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand
from requestbuilder.response import PaginatedResponse


class DescribeAlarms(CloudWatchRequest, TabifyingCommand):
    DESCRIPTION = 'Describe alarms'
    ARGS = [Arg('AlarmNames.member', metavar='ALARM', nargs='*',
                help='limit results to specific alarms'),
            Arg('--action-prefix', dest='ActionPrefix', metavar='PREFIX',
                help='''limit results to alarms whose actions' ARNs begin with
                a specific string'''),
            Arg('--alarm-name-prefix', dest='AlarmNamePrefix',
                metavar='PREFIX', help='''limit results to alarms whose names
                begin with a specific string'''),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the alarms' info"),
            Arg('--state-value', dest='StateValue',
                choices=('OK', 'ALARM', 'INSUFFICIENT_DATA'),
                help='limit results to alarms in a specific state')]
    LIST_TAGS = ['MetricAlarms', 'AlarmActions', 'Dimensions',
                 'InsufficientDataActions', 'OKActions']

    def main(self):
        return PaginatedResponse(self, (None,), ('MetricAlarms',))

    def prepare_for_page(self, page):
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for alarm in result.get('MetricAlarms', []):
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
