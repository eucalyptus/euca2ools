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

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.argtypes import flexible_bool
from euca2ools.commands.ec2 import EC2Request


class ModifyVpcAttribute(EC2Request):
    DESCRIPTION = 'Modify an attribute of a VPC'
    ARGS = [Arg('-c', '--vpc', dest='VpcId', metavar='VPC',
                help='ID of the VPC to modify (required)'),
            Arg('positional_vpc', nargs='?', route_to=None,
                help=argparse.SUPPRESS),
            MutuallyExclusiveArgList(
                Arg('-d', '--dns-hostnames', dest='EnableDnsHostnames.Value',
                    metavar='(true|false)', type=flexible_bool, help='''enable
                    or disable assignment of DNS names to instances'''),
                Arg('-s', '--dns-support', dest='EnableDnsSupport.Value',
                    metavar='(true|false)', type=flexible_bool,
                    help='enable or disable DNS resolution'))
            .required()]

    def configure(self):
        EC2Request.configure(self)
        if self.args.get('positional_vpc'):
            if self.params.get('VpcId'):
                # Shouldn't be supplied both positionally and optionally
                raise ArgumentError('unrecognized arguments: {0}'.format(
                    self.args['positional_vpc']))
            self.params['VpcId'] = self.args['positional_vpc']
        if not self.params.get('VpcId'):
            raise ArgumentError('argument -c/--vpc is required')
