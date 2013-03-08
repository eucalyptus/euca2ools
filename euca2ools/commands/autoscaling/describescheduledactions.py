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

from euca2ools.commands.autoscaling import AutoScalingRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand
from requestbuilder.response import PaginatedResponse


class DescribeScheduledActions(AutoScalingRequest, TabifyingCommand):
    DESCRIPTION = 'Describe scheduled auto-scaling group actions'
    ARGS = [Arg('ScheduledActionNames.member', metavar='ACTION', nargs='*',
                help='limit results to specific actions'),
            Arg('-g', '--group', dest='AutoScalingGroupName',
                metavar='ASGROUP'),
            Arg('--start-time', dest='StartTime',
                metavar='YYYY-MM-DDThh:mm:ssZ', help='''earliest start time to
                return scheduled actions for.  This is ignored when specific
                action names are provided.'''),
            Arg('--end-time', dest='EndTime',
                metavar='YYYY-MM-DDThh:mm:ssZ', help='''latest start time to
                return scheduled actions for.  This is ignored when specific
                action names are provided.'''),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the scheduled actions' info")]
    LIST_TAGS = ['ScheduledUpdateGroupActions']

    def main(self):
        return PaginatedResponse(self, (None,),
                                 ('ScheduledUpdateGroupActions',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for action in result.get('ScheduledUpdateGroupActions', []):
            bits = ['UPDATE-GROUP-ACTION']
            bits.append(action.get('AutoScalingGroupName'))
            bits.append(action.get('ScheduledActionName'))
            bits.append(action.get('StartTime'))
            bits.append(action.get('Recurrence'))
            bits.append(action.get('MinSize'))
            bits.append(action.get('MaxSize'))
            bits.append(action.get('DesiredCapacity'))
            if self.args['show_long']:
                bits.append(action.get('ScheduledActionARN'))
            print self.tabify(bits)
