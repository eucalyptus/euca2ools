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
from requestbuilder import Arg


class CreateRouteTable(EucalyptusRequest):
    DESCRIPTION = 'Create route table for VPC'
    ARGS = [Arg('VpcId', metavar='VPC',
                help='vpc id to create route table (required)')]
    LIST_TAGS = ['routeSet', 'associationSet']

    def print_result(self, result):
        rt = result.get('routeTable')
        print self.tabify((
            'ROUTETABLE', rt.get('routeTableId'),
            rt.get('vpcId')))

        for entry in rt.get('routeSet', []):
            self.print_entry(entry, rt.get('routeTableId'))
        for entry in rt.get('associationSet', []):
            self.print_assoc(entry, rt.get('routeTableId'))

    def print_entry(self, entry, rt_id):
        print self.tabify((
            'ROUTEENTRY', rt_id,
            entry.get('destinationCidrBlock'),
            entry.get('gatewayId'),
            entry.get('instanceId'),
            entry.get('state')))

    def print_assoc(self, entry, rt_id):
        print self.tabify((
            'ASSOCIATION', rt_id,
            entry.get('routeTableAssociationId'),
            entry.get('subnetId'),
            entry.get('main')))
