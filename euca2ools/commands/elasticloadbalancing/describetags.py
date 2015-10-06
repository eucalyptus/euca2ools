# Copyright 2015 Eucalyptus Systems, Inc.
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
from requestbuilder.mixins.formatting import TableOutputMixin

from euca2ools.commands.elasticloadbalancing import ELBRequest


class DescribeTags(ELBRequest, TableOutputMixin):
    DESCRIPTION = 'Show the tags associated with one or more load balancers'
    ARGS = [Arg('LoadBalancerNames.member', metavar='ELB', nargs='+',
                help='load balancer(s) to show tags for (required)')]
    LIST_TAGS = ['TagDescriptions', 'Tags']

    def print_result(self, result):
        table = self.get_table(('TAG', 'type', 'name', 'key', 'value'))
        for desc in result.get('TagDescriptions') or []:
            lb_name = desc.get('LoadBalancerName')
            for tag in desc.get('Tags') or []:
                table.add_row(('TAG', 'load-balancer', lb_name,
                               tag.get('Key'), tag.get('Value')))
        print table
