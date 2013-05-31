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

from euca2ools.commands.elasticloadbalancing import ELBRequest
from requestbuilder import Arg
from requestbuilder.mixins import TabifyingMixin


class DescribeLoadBalancerPolicyTypes(ELBRequest, TabifyingMixin):
    DESCRIPTION = 'Show information about load balancer policy types'
    ARGS = [Arg('PolicyTypeNames.member', metavar='POLTYPE', nargs='*',
                help='limit results to specific policy types'),
            Arg('--show-long', action='store_true', route_to=None,
                help="show all of the policy types' info")]
    LIST_TAGS = ['PolicyTypeDescriptions', 'PolicyAttributeTypeDescriptions']

    def print_result(self, result):
        for poltype in result.get('PolicyTypeDescriptions', []):
            bits = ['POLICY_TYPE', poltype.get('PolicyTypeName'),
                    poltype.get('Description')]
            if self.args['show_long']:
                attrs = []
                for attr in poltype.get('PolicyAttributeTypeDescriptions', []):
                    elem_map = (('name', 'AttributeName'),
                                ('description', 'Description'),
                                ('type', 'AttributeType'),
                                ('default-value', 'DefaultValue'),
                                ('cardinality', 'Cardinality'))
                    attr_bits = []
                    for name, xmlname in elem_map:
                        attr_bits.append('='.join((name,
                                                   attr.get(xmlname) or '')))
                    attrs.append('{' + ','.join(attr_bits) + '}')
                bits.append(','.join(attrs))
            print self.tabify(bits)
