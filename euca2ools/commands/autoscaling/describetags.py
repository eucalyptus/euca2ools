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
from euca2ools.commands.autoscaling.argtypes import autoscaling_filter_def
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin
from requestbuilder.response import PaginatedResponse


class DescribeTags(AutoScalingRequest, TabifyingMixin):
    DESCRIPTION = 'Describe auto-scaling tags'
    ARGS = [Arg('--filter', dest='Filters.member',type=autoscaling_filter_def,
                metavar='NAME=VALUE,...', action='append',
                help='restrict results to those that meet criteria')]
    LIST_TAGS = ['Tags']

    def main(self):
        return PaginatedResponse(self, (None,), ('Tags',))

    def prepare_for_page(self, page):
        # Pages are defined by NextToken
        self.params['NextToken'] = page

    def get_next_page(self, response):
        return response.get('NextToken') or None

    def print_result(self, result):
        for tag in result.get('Tags', []):
            print self.tabify(('TAG', tag.get('ResourceId'),
                               tag.get('ResourceType'), tag.get('Key'),
                               tag.get('Value'), tag.get('PropagateAtLaunch')))
