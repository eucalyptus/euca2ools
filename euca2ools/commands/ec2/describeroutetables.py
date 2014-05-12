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

from euca2ools.commands.ec2 import EC2Request
from requestbuilder import Arg


class DescribeRouteTables(EC2Request):
    DESCRIPTION = 'Describe route tables'
    ARGS = [Arg('RouteTableId', metavar='ROUTETABLE', nargs='*',
                help='limit results to specific route tables'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all route tables')]
    LIST_TAGS = ['routeTableSet', 'routeSet', 'associationSet']

    def print_result(self, result):
        tables = {}
        for table in result.get('routeTableSet', []):
            tables.setdefault(table['routeTableId'], table)

        for rt_id, table in sorted(tables.iteritems()):
            self.print_tables(table)

    def print_tables(self, table):
        print self.tabify((
            'ROUTETABLE', table.get('routeTableId'),
            table.get('vpcId')))
        for entry in table.get('routeSet', []):
            self.print_entry(entry, table.get('routeTableId'))
        for assoc in table.get('associationSet', []):
            self.print_association(assoc, table.get('routeTableId'))

    def print_entry(self, entry, rt_id):
        next_hop = 'local'
        if entry.get('gatewayId'):
            next_hop = entry.get('gatewayId')
        elif entry.get('instanceId'):
            next_hop = entry.get('instanceId')

        print self.tabify((
            'ROUTE',
            next_hop,
            entry.get('state'),
            entry.get('destinationCidrBlock'),
            entry.get('origin')))

    def print_association(self, entry, rt_id):
        main = ''
        if entry.get('main'):
            main = 'main'
        print self.tabify((
            'ASSOCIATION',
            entry.get('routeTableAssociationId'),
            main))
