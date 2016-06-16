# Copyright (c) 2013-2016 Hewlett Packard Enterprise Development LP
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

from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse

from euca2ools.commands.autoscaling import AutoScalingRequest


class DescribePolicies(AutoScalingRequest, TabifyingMixin):
    DESCRIPTION = 'Describe auto-scaling policies'
    ARGS = [Arg('PolicyNames.member', metavar='POLICY', nargs='*',
                help='limit results to specific auto-scaling policies'),
            Arg('-g', '--auto-scaling-group', dest='AutoScalingGroupName',
                metavar='ASGROUP'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the policies' info")]
    LIST_TAGS = ['ScalingPolicies', 'Alarms']

    def main(self):
        return PaginatedResponse(self, (None,), ('ScalingPolicies',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    # pylint: disable=no-self-use
    def get_next_page(self, response):
        return response.get('NextToken') or None
    # pylint: enable=no-self-use

    def print_result(self, result):
        for policy in result.get('ScalingPolicies', []):
            bits = ['SCALING-POLICY',
                    policy.get('AutoScalingGroupName'),
                    policy.get('PolicyName'),
                    policy.get('ScalingAdjustment')]
            if self.args['show_long']:
                bits.append(policy.get('MinAdjustmentStep'))
            bits.append(policy.get('AdjustmentType'))
            if self.args['show_long']:
                bits.append(policy.get('Cooldown'))
            bits.append(policy.get('PolicyARN'))
            print self.tabify(bits)
