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


class DescribeSecurityGroups(EucalyptusRequest):
    DESCRIPTION = 'Describe security groups'
    ARGS = [Arg('GroupName', metavar='groupname', nargs='*',
                help='Name of group to display'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all security groups')]
    LIST_TAGS = ['securityGroupInfo', 'ipPermissions', 'ipPermissionsEgress']

    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('all', False):
            if self.args.get('AclId'):
                raise ArgumentError('argument -a/--all: not allowed with '
                                    'a list of security groups')

    def print_result(self, result):
        groups = {}
        for group in result.get('securityGroupInfo', []):
            groups.setdefault(group['groupId'], group)

        for group_id, group in sorted(groups.iteritems()):
            self.print_groups(group)

    def print_groups(self, group):
        print self.tabify((
            'SECURITYGROUP', 
            group.get('groupId'),
            group.get('groupName'),
            group.get('groupDescription'),
            group.get('vpcId')))
        for ingress in group.get('ipPermissions', []):
            self.print_entry(entry, , 'ipPermissions', group.get('groupId'))
        for egress in group.get('ipPermissionsEgress', []):
            self.print_entry(entry, 'ipPermissionsEgress', group.get('groupId'))

    def print_entry(self, entry, direction, group_id):
        print self.tabify((
            'ENTRY', direction,
            entry.get('ipProtocol'),
            entry.get('fromPort'),
            entry.get('toPort'),
            entry.get('groups'),
            entry.get('ipRanges'),
