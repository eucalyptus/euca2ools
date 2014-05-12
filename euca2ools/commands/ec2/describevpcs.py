# Copyright 2013-2014 Eucalyptus Systems, Inc.
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


class DescribeVpcs(EC2Request):
    DESCRIPTION = 'Show information about VPCs'
    ARGS = [Arg('VpcId', metavar='VPC', nargs='*',
                help='limit results to specific VPCs')]
    FILTERS = [Filter('cidr', help="the VPC's CIDR address block"),
               Filter('dhcp-options-id', help='ID of the set of DHCP options'),
               Filter('isDefault', help='whether the VPC is a default VPC'),
               Filter('state'),
               Filter('tag-key', help='key of a tag assigned to the VPC'),
               Filter('tag-value', help='value of a tag assigned to the VPC'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('vpc-id', help="the VPC's ID")]
    LIST_TAGS = ['tagSet', 'vpcSet']

    def print_result(self, result):
        for vpc in result.get('vpcSet') or []:
            self.print_vpc(vpc)
