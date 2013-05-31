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
from requestbuilder import Arg, MutuallyExclusiveArgList


def statistic_set(set_as_str):
    pairs = {}
    for pair in set_as_str.split(','):
        try:
            key, val = pair.split('=')
        except ValueError:
            raise argparse.ArgumentTypeError(
                'statistic set must have format KEY1=VALUE1,...')
        try:
            pairs[key] = float(val)
        except ValueError:
            raise argparse.ArgumentTypeError('value "{0}" must be numeric'
                                             .format(val))
    for field in ('Maximum', 'Minimum', 'SampleCount', 'Sum'):
        if field not in pairs:
            raise argparse.ArgumentTypeError(
                'value for statistic "{0}" is required'.format(field))
    return pairs


class PutMetricData(CloudWatchRequest):
    DESCRIPTION = 'Add data points or statistics to a metric'
    ARGS = [Arg('-m', '--metric-name', dest='MetricData.member.1.MetricName',
                metavar='METRIC', required=True,
                help='name of the metric to add data points to (required)'),
            Arg('-n', '--namespace', dest='Namespace', required=True,
                help="the metric's namespace (required)"),
            MutuallyExclusiveArgList(True,
                Arg('-v', '--value', dest='MetricData.member.1.Value',
                    metavar='FLOAT', type=float,
                    help='data value for the metric'),
                Arg('-s', '--statistic-values', '--statisticValues',
                    dest='MetricData.member.1.StatisticValues',
                    type=statistic_set, metavar=('Maximum=FLOAT,Minimum=FLOAT,'
                    'SampleCount=FLOAT,Sum=FLOAT'), help='''statistic values
                    for the metric.  Values for Maximum, Minimum, SampleCount,
                    and Sum are all required.''')),
            Arg('-d', '--dimensions', dest='Dimensions.member',
                metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help='the dimensions of the metric to add data points to'),
            Arg('-t', '--timestamp', dest='MetricData.member.1.Timestamp',
                metavar='YYYY-MM-DDThh:mm:ssZ',
                help='timestamp of the data point'),
            Arg('-u', '--unit', dest='MetricData.member.1.Unit',
                metavar='UNIT', help='unit the metric is being reported in')]
