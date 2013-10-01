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
from requestbuilder import Arg, Filter, GenericTagFilter
from requestbuilder.exceptions import ArgumentError


class DescribeSubnets(EucalyptusRequest):
    DESCRIPTION = 'Shows information about subnets.'
    ARGS = [Arg('SubnetId', metavar='SUBNET', nargs='*',
                help='limit results to specific subnets'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all subnets')]
    LIST_TAGS = ['subnetSet']

    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('all', False):
            if self.args.get('SubnetId'):
                raise ArgumentError('argument -a/--all: not allowed with '
                                    'a list of subnets')

    def print_result(self, result):
        subnets = {}
        for subnet in result.get('subnetSet', []):
            subnets.setdefault(subnet['subnetId'], subnet)

        for subnet_id, subnet in sorted(subnets.iteritems()):
            self.print_subnets(subnet)

    def print_subnets(self, subnet):
        print self.tabify((
            'SUBNET', subnet.get('subnetId'),
            subnet.get('vpcId'),
            subnet.get('cidrBlock')))
