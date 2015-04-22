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

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.monitoring import CloudWatchRequest
from euca2ools.commands.monitoring.argtypes import cloudwatch_dimension
from requestbuilder import Arg


class PutMetricAlarm(CloudWatchRequest):
    DESCRIPTION = 'Create or update an alarm'
    ARGS = [Arg('AlarmName', metavar='ALARM',
                help='name of the alarm (required)'),
            Arg('--comparison-operator', dest='ComparisonOperator',
                choices=('GreaterThanOrEqualToThreshold',
                         'GreaterThanThreshold', 'LessThanThreshold',
                         'LessThanOrEqualToThreshold'), required=True,
                help='''arithmetic operator with which the comparison with the
                threshold will be made (required)'''),
            Arg('--evaluation-periods', dest='EvaluationPeriods', type=int,
                metavar='COUNT', required=True, help='''number of consecutive
                periods for which the value of the metric needs to be compared
                to the threshold (required)'''),
            Arg('--metric-name', dest='MetricName', metavar='METRIC',
                required=True,
                help="name for the alarm's associated metric (required)"),
            Arg('--namespace', dest='Namespace', metavar='NAMESPACE',
                required=True,
                help="namespace for the alarm's associated metric (required)"),
            Arg('--period', dest='Period', metavar='SECONDS', type=int,
                required=True, help='''period over which the specified
                statistic is applied (required)'''),
            Arg('--statistic', dest='Statistic', required=True,
                choices=('Average', 'Maximum', 'Minimum', 'SampleCount',
                         'Sum'),
                help='statistic on which to alarm (required)'),
            Arg('--threshold', dest='Threshold', metavar='FLOAT', type=float,
                required=True,
                help='value to compare the statistic against (required)'),
            Arg('--actions-enabled', dest='ActionsEnabled',
                choices=('true', 'false'), help='''whether this alarm's actions
                should be executed when it changes state'''),
            Arg('--alarm-actions', dest='AlarmActions.member',
                metavar='ARN1,ARN2,...', type=delimited_list(','),
                help='''ARNs of SNS topics to publish to when the alarm changes
                to the ALARM state'''),
            Arg('--alarm-description', dest='AlarmDescription',
                metavar='DESCRIPTION', help='description of the alarm'),
            Arg('-d', '--dimensions', dest='Dimensions.member',
                metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help="dimensions for the alarm's associated metric"),
            Arg('--insufficient-data-actions', metavar='ARN1,ARN2,...',
                dest='InsufficientDataActions.member',
                type=delimited_list(','), help='''ARNs of SNS topics to publish
                to when the alarm changes to the INSUFFICIENT_DATA state'''),
            Arg('--ok-actions', dest='OKActions.member',
                metavar='ARN1,ARN2,...', type=delimited_list(','),
                help='''ARNs of SNS topics to publish to when the alarm changes
                to the OK state'''),
            Arg('--unit', dest='Unit',
                help="unit for the alarm's associated metric")]
