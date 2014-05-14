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

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.ec2 import EC2Request


class CreateRoute(EC2Request):
    DESCRIPTION = 'Add a route to a VPC routing table'
    API_VERSION = '2014-02-01'
    ARGS = [Arg('RouteTableId', metavar='RTABLE',
                help='ID of the route table to add the route to (required)'),
            Arg('-d', '--dest-cidr', dest='DestinationCidrBlock',
                metavar='CIDR', required=True,
                help='CIDR address block the route should affect (required)'),
            MutuallyExclusiveArgList(
                Arg('-g', '--gateway-id', dest='GatewayId', metavar='GATEWAY',
                    help='ID of an Internet gateway to target'),
                Arg('-i', '--instance', dest='InstanceId', metavar='INSTANCE',
                    help='ID of a NAT instance to target'),
                Arg('-n', '--network-interface', dest='NetworkInterfaceId',
                    help='ID of a network interface to target'),
                Arg('-p', '--vpc-peering-connection', metavar='PEERCON',
                    dest='VpcPeeringConnectionId',
                    help='ID of a VPC peering connection to target'))
            .required()]

    def print_result(self, result):
        target = (self.args.get('GatewayId') or self.args.get('InstanceId') or
                  self.args.get('NetworkInterfaceId') or
                  self.args.get('VpcPeeringConnectionId'))
        print self.tabify(('ROUTE', target, self.args['DestinationCidrBlock']))
