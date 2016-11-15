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


class DescribeVpcPeeringConnections(EC2Request):
    DESCRIPTION = 'Show information about VPC peering connections'
    ARGS = [Arg('VpcPeeringConnectionId', metavar='PEERCONN', nargs='*',
                help='limit results to specific VPC peering connections')]
    FILTERS = [Filter('accepter-vpc-info.cidr-block',
                      help="the peer VPC's CIDR address block"),
               Filter('accepter-vpc-info.owner-id',
                      help="the peer VPC's owner's account ID"),
               Filter('accepter-vpc-info.vpc-id', help="the peer VPC's ID"),
               Filter('expiration-time',
                      help='when the peering connection request expires'),
               Filter('requester-vpc-info.cidr-block',
                      help="the requester VPC's CIDR address block"),
               Filter('requester-vpc-info.owner-id',
                      help="the requester VPC's owner's account ID"),
               Filter('requester-vpc-info.vpc-id',
                      help="the requester VPC's ID"),
               Filter('status-code', help='''the peering connection's status
                      (active, deleted, expired, failed, pending-acceptance,
                      provisioning, rejected)'''),
               Filter('tag-key',
                      help='key of a tag assigned to the peering connection'),
               Filter('tag-value', help='''value of a tag assigned to the
                      peering connection'''),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('vpc-peering-connection-id',
                      help="the peering connection's ID")]
    LIST_TAGS = ['tagSet', 'vpcPeeringConnectionSet']

    def print_result(self, result):
        for pcx in result.get('vpcPeeringConnectionSet') or []:
            self.print_peering_connection(pcx)
