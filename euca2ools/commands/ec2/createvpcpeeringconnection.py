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

from requestbuilder import Arg

from euca2ools.commands.ec2 import EC2Request


class CreateVpcPeeringConnection(EC2Request):
    DESCRIPTION = ('Request a peering connection between two VPCs\n\nThe '
                   'owner of the VPC you wish to peer with must accept '
                   'the peering request to activate the peering connection')
    ARGS = [Arg('-c', '--vpc', dest='VpcId', metavar='VPC', required=True,
                help='''the VPC to request a peering connection from
                (required)'''),
            Arg('-p', '--peer-vpc', dest='PeerVpcId', metavar='VPC',
                required=True,
                help='the VPC to request a peering connection to (required)'),
            Arg('-o', '--peer-owner-id', dest='PeerOwnerId', metavar='ACCOUNT',
                help='''account ID of the peer VPC's owner (default: current
                user's account ID)''')]
    LIST_TAGS = ['tagSet']

    def print_result(self, result):
        self.print_peering_connection(result.get('vpcPeeringConnection') or {})
