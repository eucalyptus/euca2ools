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
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeScalingActivities(AutoScalingRequest, TabifyingMixin):
    DESCRIPTION = 'Describe past and current auto-scaling activities'
    ARGS = [Arg('ActivityIds.member', metavar='ACTIVITY', nargs='*',
                help='limit results to specific auto-scaling activities'),
            Arg('-g', '--auto-scaling-group', dest='AutoScalingGroupName',
                metavar='ASGROUP', help='''name of an Auto Scaling group by
                which to filter the request'''),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the groups' info")]
    LIST_TAGS = ['Activities']

    def main(self):
        return PaginatedResponse(self, (None,), ('Activities',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for activity in result.get('Activities', []):
            bits = ['ACTIVITY']
            bits.append(activity.get('ActivityId'))
            bits.append(activity.get('EndTime'))
            bits.append(activity.get('AutoScalingGroupName'))
            bits.append(activity.get('StatusCode'))
            bits.append(activity.get('StatusMessage'))
            if self.args['show_long']:
                bits.append(activity.get('Cause'))
                bits.append(activity.get('Progress'))
                bits.append(activity.get('Description'))
                # The AWS tool refers to this as "UPDATE-TIME", but seeing as
                # the API doesn't actually have anything like that, the process
                # of elimination dictates that this be the Details element in
                # the response instead.
                bits.append(activity.get('Details'))
                bits.append(activity.get('StartTime'))
            print self.tabify(bits)
