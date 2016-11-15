# Copyright (c) 2014-2016 Hewlett Packard Enterprise Development LP
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


class DescribeInternetGateways(EC2Request):
    DESCRIPTION = 'Describe one or more VPC Internet gateways'
    ARGS = [Arg('InternetGatewayId', metavar='IGATEWAY', nargs='*',
                help='limit results to one or more Internet gateways')]
    FILTERS = [Filter('attachment.state', help='''if the Internet gateway is
                      attached to a VPC, its attachment state (available)'''),
               Filter('attachment.vpc-id', help='''ID of the VPC the Internet
                      gateway is attached to'''),
               Filter('internet-gateway-id', "the Internet gateway's ID"),
               Filter('tag-key',
                      help='key of a tag assigned to the Internet gateway'),
               Filter('tag-value',
                      help='value of a tag assigned to the Internet gateway'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination')]

    LIST_TAGS = ['attachmentSet', 'internetGatewaySet', 'tagSet']

    def print_result(self, result):
        for igw in result.get('internetGatewaySet') or []:
            self.print_internet_gateway(igw)
