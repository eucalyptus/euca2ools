# Copyright 2014 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg, Filter, GenericTagFilter

from euca2ools.commands.ec2 import EC2Request


class DescribeVpnGateways(EC2Request):
    DESCRIPTION = 'Show information about virtual private gateways'
    ARGS = [Arg('VpnGatewayId', metavar='VGATEWAY', nargs='*',
                help='limit results to specific virtual private gateways')]
    FILTERS = [Filter('attachment.state',
                      help='state of attachment with a VPC'),
               Filter('attachment.vpc-id', help='''ID of a VPC the virtual
                      private gateway is attached to'''),
               Filter('availability-zone', help='''availability zone in
                      which the virtual private gateway resides'''),
               Filter('tag-key',
                      help='key of a tag assigned to the customer gateway'),
               Filter('tag-value',
                      help='value of a tag assigned to the customer gateway'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('type',
                      help='the type of virtual private gateway (ipsec.1)'),
               Filter('vpn-gateway-id',
                      help='ID of the virtual private gateway')]

    LIST_TAGS = ['attachments', 'vpnGatewaySet', 'tagSet']

    def print_result(self, result):
        for vgw in result.get('vpnGatewaySet', []):
            self.print_vpn_gateway(vgw)
