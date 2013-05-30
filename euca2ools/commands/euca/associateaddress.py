# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError


class AssociateAddress(EucalyptusRequest):
    DESCRIPTION = 'Associate an elastic IP address with a running instance'
    ARGS = [MutuallyExclusiveArgList(True,
                Arg('-i', '--instance-id', dest='InstanceId',
                    metavar='INSTANCE', help='''ID of the instance to associate
                    the address with'''),
                Arg('-n', '--network-interface', dest='NetworkInterfaceId',
                    metavar='INTERFACE', help='''[VPC only] network interface
                    to associate the address with''')),
            Arg('PublicIp', metavar='ADDRESS', nargs='?', help='''[Non-VPC
                only] IP address to associate (required)'''),
            Arg('-a', '--allocation-id', dest='AllocationId', metavar='ALLOC',
                help='[VPC only] VPC allocation ID (required)'),
            Arg('-p', '--private-ip-address', dest='PrivateIpAddress',
                metavar='ADDRESS', help='''[VPC only] the private address to
                associate with the address being associated in the VPC
                (default: primary private IP)'''),
            Arg('--allow-reassociation', dest='AllowReassociation',
                action='store_const', const='true',
                help='''[VPC only] allow the address to be associated even if
                it is already associated with another interface''')]

    def configure(self):
        EucalyptusRequest.configure(self)
        if (self.args.get('PublicIp') is not None and
            self.args.get('AllocationId') is not None):
            # Can't be both EC2 and VPC
            raise ArgumentError(
                'argument -a/--allocation-id: not allowed with an IP address')
        if (self.args.get('PublicIp') is None and
            self.args.get('AllocationId') is None):
            # ...but we still have to be one of them
            raise ArgumentError(
                'argument -a/--allocation-id or an IP address is required')

    def print_result(self, result):
        if self.args.get('AllocationId'):
            # VPC
            print self.tabify(('ADDRESS', self.args.get('InstanceId'),
                               self.args.get('AllocationId'),
                               result.get('associationId'),
                               self.args.get('PrivateIpAddress')))
        else:
            # EC2
            print self.tabify(('ADDRESS', self.args.get('PublicIp'),
                               self.args.get('InstanceId')))
