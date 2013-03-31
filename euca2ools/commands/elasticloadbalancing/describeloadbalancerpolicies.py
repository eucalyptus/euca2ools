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

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.elasticloadbalancing import ELBRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingCommand


class DescribeLoadBalancerPolicies(ELBRequest, TabifyingCommand):
    DESCRIPTION = 'Show information about load balancer policies'
    ARGS = [Arg('LoadBalancerName', metavar='ELB', nargs='?', help='''show
                policies associated with a specific load balancer (default:
                only describe sample policies provided by the service)'''),
            Arg('-p', '--policy-names', dest='PolicyNames.member',
                metavar='POLICY1,POLICY2,...', type=delimited_list(','),
                help='limit results to specific policies'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the policies' info")]
    LIST_TAGS = ['PolicyDescriptions', 'PolicyAttributeDescriptions']

    def print_result(self, result):
        for policy in result.get('PolicyDescriptions', []):
            bits = ['POLICY', policy.get('PolicyName'),
                    policy.get('PolicyTypeName')]
            if self.args['show_long']:
                attrs = []
                for attr in policy.get('PolicyAttributeDescriptions', []):
                    attrs.append('{{name={0},value={1}}}'.format(
                        attr.get('AttributeName'), attr.get('AttributeValue')))
                if len(attrs) > 0:
                    bits.append(','.join(attrs))
                else:
                    bits.append(None)
            print self.tabify(bits)
