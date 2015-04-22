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

import argparse
from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.monitoring import CloudWatchRequest
from euca2ools.commands.monitoring.argtypes import cloudwatch_dimension
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeAlarmsForMetric(CloudWatchRequest, TabifyingMixin):
    DESCRIPTION = ('Describe alarms for a single metric.\n\nNote that all '
                   "of an alarm's metrics must match exactly to obtain any "
                   'results.')
    ARGS = [Arg('--metric-name', dest='MetricName', metavar='METRIC',
                required=True, help='name of the metric (required)'),
            Arg('--namespace', dest='Namespace', metavar='NAMESPACE',
                required=True, help='namespace of the metric (required)'),
            # --alarm-description is supported by the tool, but not the service
            Arg('--alarm-description', route_to=None, help=argparse.SUPPRESS),
            Arg('--dimensions', dest='Dimensions.member',
                metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help='dimensions of the metric'),
            Arg('--period', dest='Period', metavar='SECONDS',
                help='period over which statistics are applied'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the alarms' info"),
            Arg('--statistic', dest='Statistic',
                choices=('Average', 'Maximum', 'Minimum', 'SampleCount',
                         'Sum'),
                help='statistic of the metric on which to trigger alarms'),
            Arg('--unit', dest='Unit',
                help='unit of measurement for statistics')]
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
            self.print_alarm(alarm)
