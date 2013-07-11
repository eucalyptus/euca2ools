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

from euca2ools.commands.autoscaling import AutoScalingRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeAutoScalingGroups(AutoScalingRequest, TabifyingMixin):
    DESCRIPTION = 'Describe auto-scaling groups'
    ARGS = [Arg('AutoScalingGroupNames.member', metavar='ASGROUP',
                nargs='*',
                help='limit results to specific auto-scaling groups'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the groups' info")]
    LIST_TAGS = ['AutoScalingGroups', 'AvailabilityZones', 'EnabledMetrics',
                 'Instances', 'LoadBalancerNames', 'SuspendedProcesses',
                 'Tags', 'TerminationPolicies']

    def main(self):
        return PaginatedResponse(self, (None,), ('AutoScalingGroups',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        lines = []
        for group in result.get('AutoScalingGroups', []):
            bits = ['AUTO-SCALING-GROUP',
                    group.get('AutoScalingGroupName'),
                    group.get('LaunchConfigurationName'),
                    ','.join(group.get('AvailabilityZones'))]
            if self.args['show_long']:
                bits.append(group.get('CreatedTime'))
            balancers = group.get('LoadBalancerNames')
            if balancers:
                bits.append(','.join(balancers))
            else:
                bits.append(None)
            if self.args['show_long']:
                bits.append(group.get('HealthCheckType'))
            bits.append(group.get('MinSize'))
            bits.append(group.get('MaxSize'))
            bits.append(group.get('DesiredCapacity'))
            if self.args['show_long']:
                bits.append(group.get('DefaultCooldown'))
                bits.append(group.get('HealthCheckGracePeriod'))
                bits.append(group.get('VPCZoneIdentifier'))
                bits.append(group.get('PlacementGroup'))
                bits.append(group.get('AutoScalingGroupARN'))
            policies = group.get('TerminationPolicies')
            if policies:
                bits.append(','.join(policies))
            else:
                bits.append(None)
            lines.append(self.tabify(bits))
            for instance in group.get('Instances', []):
                lines.append(self._get_tabified_instance(instance))
            scale_group = group.get('AutoScalingGroupName')
            for process in group.get('SuspendedProcesses', []):
                lines.append(self._get_tabified_suspended_process(process,
                                                                  scale_group))
            for metric in group.get('EnabledMetrics', []):
                lines.append(self._get_tabified_metric(metric))
        for line in lines:
            print line

    def _get_tabified_instance(self, instance):
        return self.tabify(['INSTANCE',
                            instance.get('InstanceId'),
                            instance.get('AvailabilityZone'),
                            instance.get('LifecycleState'),
                            instance.get('HealthStatus'),
                            instance.get('LaunchConfigurationName')
                            ])

    def _get_tabified_suspended_process(self, process, scale_group):
        return self.tabify(['SUSPENDED-PROCESS',
                            process.get('ProcessName'),
                            process.get('SuspensionReason'),
                            scale_group
                            ])

    def _get_tabified_metric(self, metric):
        return self.tabify(['ENABLED-METRICS',
                            metric.get('Metric'),
                            metric.get('Granularity')
                            ])
