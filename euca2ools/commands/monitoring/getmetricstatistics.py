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

import datetime
from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.monitoring import CloudWatchRequest
from euca2ools.commands.monitoring.argtypes import cloudwatch_dimension
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class GetMetricStatistics(CloudWatchRequest, TabifyingMixin):
    DESCRIPTION = "Show a metric's statistics"
    ARGS = [Arg('MetricName', metavar='METRIC',
                help='name of the metric to get statistics for (required)'),
            Arg('-n', '--namespace', dest='Namespace', required=True,
                help="the metric's namespace (required)"),
            Arg('-s', '--statistics', dest='Statistics.member', required=True,
                metavar='STAT1,STAT2,...', type=delimited_list(','),
                help='the metric statistics to show (at least 1 required)'),
            Arg('--dimensions', dest='Dimensions.member',
                metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help='the dimensions of the metric to show'),
            Arg('--start-time', dest='StartTime',
                metavar='YYYY-MM-DDThh:mm:ssZ', help='''earliest time to
                retrieve data points for (default: one hour ago)'''),
            Arg('--end-time', dest='EndTime',
                metavar='YYYY-MM-DDThh:mm:ssZ', help='''latest time to retrieve
                data points for (default: now)'''),
            Arg('--period', dest='Period', metavar='SECONDS', type=int,
                help='''granularity of the returned data points (must be a
                multiple of 60)'''),
            Arg('--unit', dest='Unit', help='unit the metric is reported in')]
    LIST_TAGS = ['Datapoints']

    # noinspection PyExceptionInherit
    def configure(self):
        CloudWatchRequest.configure(self)
        if self.args.get('period'):
            if self.args['period'] <= 0:
                raise ArgumentError(
                    'argument --period: value must be positive')
            elif self.args['period'] % 60 != 0:
                raise ArgumentError(
                    'argument --period: value must be a multiple of 60')

    def main(self):
        now = datetime.datetime.utcnow()
        then = now - datetime.timedelta(hours=1)
        if not self.args.get('StartTime'):
            self.params['StartTime'] = then.strftime('%Y-%m-%dT%H:%M:%SZ')
        if not self.args.get('EndTime'):
            self.params['EndTime'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        return PaginatedResponse(self, (None,), ('Datapoints',))

    def prepare_for_page(self, page):
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        points = []
        for point in result.get('Datapoints', []):
            timestamp = point.get('Timestamp', '')
            try:
                parsed = datetime.datetime.strptime(timestamp,
                                                    '%Y-%m-%dT%H:%M:%SZ')
                timestamp = parsed.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # We'll just print it verbatim
                pass
            points.append((timestamp, point.get('SampleCount'),
                           point.get('Average'), point.get('Sum'),
                           point.get('Minimum'), point.get('Maximum'),
                           point.get('Unit')))
        for point in sorted(points):
            print self.tabify(point)
