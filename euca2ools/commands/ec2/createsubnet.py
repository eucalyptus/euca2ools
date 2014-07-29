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

import argparse

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.ec2 import EC2Request


class CreateSubnet(EC2Request):
    DESCRIPTION = 'Create a new VPC subnet'
    # We also accept CidrBlock positionally because forgetting -i is common.
    # https://eucalyptus.atlassian.net/browse/TOOLS-497
    ARGS = [Arg('positional_cidr', nargs='?', route_to=None,
                help=argparse.SUPPRESS),
            Arg('-c', '--vpc', dest='VpcId', required=True,
                help='ID of the VPC to create the new subnet in (required)'),
            Arg('-i', '--cidr', dest='CidrBlock', metavar='CIDR',
                help='CIDR address block for the new subnet (required)'),
            Arg('-z', '--availability-zone', dest='AvailabilityZone',
                help='availability zone in which to create the new subnet')]
    LIST_TAGS = ['tagSet']

    def configure(self):
        EC2Request.configure(self)
        if self.args.get('positional_cidr'):
            if self.params.get('CidrBlock'):
                # Shouldn't be supplied both positionally and optionally
                raise ArgumentError('unrecognized arguments: {0}'.format(
                    self.args['positional_cidr']))
            self.params['CidrBlock'] = self.args['positional_cidr']
        if not self.params.get('CidrBlock'):
            raise ArgumentError('argument -i/--cidr is required')

    def print_result(self, result):
        self.print_subnet(result.get('subnet') or {})
