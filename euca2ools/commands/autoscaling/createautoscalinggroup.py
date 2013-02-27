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

from requestbuilder import Arg
from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.autoscaling import AutoScalingRequest
from euca2ools.commands.autoscaling.argtypes import autoscaling_tag_def


class CreateAutoScalingGroup(AutoScalingRequest):
    DESCRIPTION = 'Create a new auto-scaling group'
    ARGS = [Arg('AutoScalingGroupName', metavar='NAME',
                help='name of the new auto-scaling group (required)'),
            Arg('-l', '--launch-configuration', dest='LaunchConfigurationName',
                metavar='LAUNCHCONFIG', required=True, help='''name of the
                launch configuration to use with the new group (required)'''),
            Arg('-M', '--max-size', dest='MaxSize', metavar='COUNT', type=int,
                required=True, help='maximum group size (required)'),
            Arg('-m', '--min-size', dest='MinSize', metavar='COUNT', type=int,
                required=True, help='minimum group size (required)'),
            Arg('--default-cooldown', dest='DefaultCooldown',
                metavar='SECONDS', type=int,
                help='''amount of time, in seconds, after a scaling activity
                        completes before any further trigger-related scaling
                        activities may start'''),
            Arg('--desired-capacity', dest='DesiredCapacity', metavar='COUNT',
                type=int,
                help='number of running instances the group should contain'),
            Arg('--grace-period', dest='HealthCheckGracePeriod',
                metavar='SECONDS', type=int, help='''number of seconds to wait
                before starting health checks on newly-created instances'''),
            Arg('--health-check-type', dest='HealthCheckType',
                choices=('EC2', 'ELB'),
                help='service to obtain health check status from'),
            Arg('--load-balancers', dest='LoadBalancerNames.member',
                metavar='ELB,ELB,...', type=delimited_list(','),
                help='comma-separated list of load balancers to use'),
            Arg('--placement-group', dest='PlacementGroup',
                help='placement group in which to launch new instances'),
            Arg('--tag', dest='Tags.member', type=autoscaling_tag_def,
                action='append', metavar=('"k=VALUE, id=VALUE, t=VALUE, '
                'v=VALUE, p={true,false}"'), help=('''
                tags to create or update.  Tags follow the following format:
                "id=resource-name, t=resource-type, k=tag-key, v=tag-val,
                p=propagate-at-launch-flag", where k is the tag's name, v is
                the tag's value, id is a resource ID, t is a resource type, and
                p is whether to propagate tags to instances created by the new
                group.  A value for 'k=' is required for each tag.  The
                remainders are optional.''')),
            Arg('--termination-policies', dest='TerminationPolicies.member',
                metavar='POLICY,POLICY,...', type=delimited_list(','),
                help='''ordered list of termination policies.  The first has
                the highest precedence.'''),
            Arg('--vpc-zone-identifier', dest='VPCZoneIdentifier',
                metavar='ZONE,ZONE,...',
                help='''comma-separated list of subnet identifiers.  If you
                specify availability zones as well, ensure the subnets'
                availability zones match the ones you specified'''),
            Arg('-z', '--availability-zones', dest='AvailabilityZones.member',
                metavar='ZONE,ZONE,...', type=delimited_list(','),
                help='''comma-separated list of availability zones for the new
                group (required unless subnets are supplied)''')]
