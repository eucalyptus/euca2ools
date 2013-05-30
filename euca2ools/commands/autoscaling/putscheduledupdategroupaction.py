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


class PutScheduledUpdateGroupAction(AutoScalingRequest):
    DESCRIPTION = 'Schedule a scaling action for an auto-scaling group'
    ARGS = [Arg('ScheduledActionName', metavar='ACTION',
                help='name of the new scheduled action'),
            Arg('-g', '--auto-scaling-group', dest='AutoScalingGroupName',
                metavar='ASGROUP', required=True, help='''auto-scaling group
                the new action should affect (required)'''),
            Arg('-b', '--start-time', dest='StartTime',
                metavar='YYYY-MM-DDThh:mm:ssZ',
                help='time for this action to start'),
            Arg('-e', '--end-time', dest='EndTime',
                metavar='YYYY-MM-DDThh:mm:ssZ',
                help='time for this action to end'),
            Arg('-r', '--recurrence', dest='Recurrence',
                metavar='"MIN HOUR DATE MONTH DAY"', help='''time when
                recurring future actions will start, in crontab format'''),
            Arg('--desired-capacity', dest='DesiredCapacity', metavar='COUNT',
                type=int, help='new capacity setting for the group'),
            Arg('--max-size', dest='MaxSize', metavar='COUNT', type=int,
                help='maximum number of instances to allow in the group'),
            Arg('--min-size', dest='MinSize', metavar='COUNT', type=int,
                help='minimum number of instances to allow in the group')]
