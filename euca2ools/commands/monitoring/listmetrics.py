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

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.monitoring import CloudWatchRequest
from euca2ools.commands.monitoring.argtypes import cloudwatch_dimension
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class ListMetrics(CloudWatchRequest, TabifyingMixin):
    DESCRIPTION = 'Show a list of monitoring metrics'
    ARGS = [Arg('-d', '--dimensions', dest='Dimensions.member',
                metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help='limit results to metrics with specific dimensions'),
            Arg('-m', '--metric-name', dest='MetricName', metavar='METRIC',
                help='limit results to a specific metric'),
            Arg('-n', '--namespace', dest='Namespace', metavar='NAMESPACE',
                help='limit results to metrics in a specific namespace')]
    LIST_TAGS = ['Metrics', 'Dimensions']

    def main(self):
        return PaginatedResponse(self, (None,), ('Metrics,'))

    def prepare_for_page(self, page):
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        out_lines = []
        for metric in sorted(result.get('Metrics', [])):
            if len(metric.get('Dimensions', [])) > 0:
                formatted_dims = ['{0}={1}'.format(dimension.get('Name'),
                                                   dimension.get('Value'))
                                  for dimension in metric['Dimensions']]
                out_lines.append((metric.get('MetricName'),
                                  metric.get('Namespace'),
                                  '{{{0}}}'.format(','.join(formatted_dims))))
            else:
                out_lines.append((metric.get('MetricName'),
                                  metric.get('Namespace'), None))
        for out_line in sorted(out_lines):
            print self.tabify(out_line)
