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

import argparse

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.ec2 import EC2Request


class AssignPrivateIpAddresses(EC2Request):
    DESCRIPTION = ('Assign one or more private IP addresses to a network '
                   'interface\n\nNote that an instance\'s type may affect '
                   'the number of addresses it can hold at once.')
    ARGS = [Arg('-n', '--network-interface', metavar='INTERFACE',
                dest='NetworkInterfaceId', help='''ID of the network interface
                to assign addresses to (required)'''),
            Arg('positional_interface', nargs='?', route_to=None,
                help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('--secondary-address', '--secondary-private-ip-address',
                    metavar='ADDRESS', dest='PrivateIpAddress',
                    action='append', help='''assign a specific secondary
                    private IP address to the network interface.  Use this
                    option multiple times to add additional addresses.'''),
                Arg('--secondary-count',
                    '--secondary-private-ip-address-count', type=int,
                    dest='SecondaryPrivateIpAddressCount', metavar='COUNT',
                    help='''automatically assign a specific number of secondary
                    private IP addresses to the network interface'''))
            .required(),
            Arg('--allow-reassignment', dest='AllowReassignment',
                action='store_true', help='''Allow addresses to be assigned
                even if they are already associated with other interfaces''')]

    def configure(self):
        EC2Request.configure(self)
        if self.args.get('positional_interface'):
            if self.params.get('NetworkInterfaceId'):
                # Shouldn't be supplied both positionally and optionally
                raise ArgumentError('unrecognized arguments: {0}'.format(
                    self.args['positional_interface']))
            self.params['NetworkInterfaceId'] = \
                self.args['positional_interface']
        if not self.params.get('NetworkInterfaceId'):
            raise ArgumentError('argument -n/--network-interface is required')
