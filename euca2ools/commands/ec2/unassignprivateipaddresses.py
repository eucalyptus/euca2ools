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

import argparse

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.ec2 import EC2Request


class UnassignPrivateIpAddresses(EC2Request):
    DESCRIPTION = ('Remove one or more private IP addresses from a '
                   'network interface')
    ARGS = [Arg('-n', '--network-interface', metavar='INTERFACE',
                dest='NetworkInterfaceId', help='''ID of the network interface
                to remove addresses from (required)'''),
            Arg('positional_interface', nargs='?', route_to=None,
                help=argparse.SUPPRESS),
            Arg('--secondary-address', '--secondary-private-ip-address',
                metavar='ADDRESS', dest='PrivateIpAddress', action='append',
                required=True, help='''an IP address to remove from the
                network interface.  Use this option multiple times to remove
                additional addresses.''')]

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
