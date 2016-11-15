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

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.ec2 import EC2Request


class CreateNetworkInterface(EC2Request):
    DESCRIPTION = 'Create a new VPC network interface'
    ARGS = [Arg('SubnetId', metavar='SUBNET', help='''subnet to create
                the new network interface in (required)'''),
            Arg('-d', '--description', dest='Description', metavar='DESC',
                help='description for the new network interface'),
            Arg('-g', '--group', dest='SecurityGroupId', metavar='GROUP',
                action='append',
                help='''ID of a security group to add the new network interface
                to.  This option may be used more than once.  Each time adds
                the network interface to an additional security group.'''),
            Arg('--private-ip-address', metavar='ADDRESS', route_to=None,
                help='''assign a specific primary private IP address to the
                new network interface'''),
            MutuallyExclusiveArgList(
                Arg('--secondary-address', '--secondary-private-ip-address',
                    metavar='ADDRESS', route_to=None, action='append',
                    help='''assign a specific secondary private IP address
                    to the new network interface.  Use this option multiple
                    times to add additional addresses.'''),
                Arg('--secondary-count',
                    '--secondary-private-ip-address-count', type=int,
                    dest='SecondaryPrivateIpAddressCount', metavar='COUNT',
                    help='''automatically assign a specific number of secondary
                    private IP addresses to the new network interface'''))]
    LIST_TAGS = ['groupSet', 'privateIpAddressesSet']

    def preprocess(self):
        addrs = []
        if self.args.get('private_ip_address'):
            addrs.append({'PrivateIpAddress': self.args['private_ip_address'],
                          'Primary': True})
        for addr in self.args.get('secondary_private_ip_address') or []:
            addrs.append({'PrivateIpAddress': addr, 'Primary': False})
        self.params['PrivateIpAddresses'] = addrs

    def print_result(self, result):
        self.print_interface(result.get('networkInterface') or {})
