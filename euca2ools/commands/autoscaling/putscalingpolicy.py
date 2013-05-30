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


class PutScalingPolicy(AutoScalingRequest):
    DESCRIPTION = "Create or update an auto-scaling group's scaling policy"
    ARGS = [Arg('PolicyName', metavar='POLICY',
                help='name of the policy to create or update (required)'),
            Arg('-g', '--auto-scaling-group', dest='AutoScalingGroupName',
                metavar='ASGROUP', required=True,
                help='''name of the auto-scaling group the policy is associated
                with (required)'''),
            Arg('-a', '--adjustment', dest='ScalingAdjustment',
                metavar='SCALE', type=int, required=True,
                help='''amount to scale the group's capacity of the group.  Use
                a negative value, as in "--adjustment=-1", to decrease
                capacity. (required)'''),
            Arg('-t', '--type', dest='AdjustmentType', required=True,
                choices=('ChangeInCapacity', 'ExactCapacity',
                         'PercentChangeInCapacity'), help='''whether the
                adjustment is the new desired size or an increment to the
                group's current capacity. An increment can either be a fixed
                number or a percentage of current capacity.  (required)'''),
            Arg('--cooldown', dest='Cooldown', metavar='SECONDS', type=int,
                help='''waiting period after successful auto-scaling activities
                during which later auto-scaling activities will not
                execute'''),
            Arg('-s', '--min-adjustment-step', dest='MinAdjustmentStep',
                type=int, metavar='PERCENT',
                help='''for a PercentChangeInCapacity type policy, guarantee
                that this policy will change the group's desired capacity by at
                least this much''')]

    def print_result(self, result):
        print result.get('PolicyARN')
