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
from euca2ools.commands.autoscaling import AutoScalingRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeAutoScalingInstances(AutoScalingRequest, TabifyingMixin):
    DESCRIPTION = 'Describe instances in auto-scaling groups'
    ARGS = [Arg('InstanceIds.member', metavar='INSTANCE', nargs='*',
                help='limit results to specific instances'),
            Arg('--show-long', action='store_true', route_to=None,
                help=argparse.SUPPRESS)]  # doesn't actually do anything, but
                                          # people will use it out of habit
    LIST_TAGS = ['AutoScalingInstances']

    def main(self):
        return PaginatedResponse(self, (None,), ('AutoScalingInstances',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for instance in result.get('AutoScalingInstances', []):
            bits = ['INSTANCE']
            bits.append(instance.get('InstanceId'))
            bits.append(instance.get('AutoScalingGroupName'))
            bits.append(instance.get('AvailabilityZone'))
            bits.append(instance.get('LifecycleState'))
            bits.append(instance.get('HealthStatus'))
            bits.append(instance.get('LaunchConfigurationName'))
            print self.tabify(bits)
