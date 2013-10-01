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


class DescribeNetworkAcls(EucalyptusRequest):
    DESCRIPTION = 'Describe a network ACL'
    ARGS = [Arg('AclId', metavar='ACL', nargs='*',
                help='Id of acl to display'),
            Arg('-a', '--all', action='store_true', route_to=None,
                help='describe all acls')]
    LIST_TAGS = ['networkAclSet', 'entrySet', 'associationSet']

    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('all', False):
            if self.args.get('AclId'):
                raise ArgumentError('argument -a/--all: not allowed with '
                                    'a list of acls')

    def print_result(self, result):
        acls = {}
        for acl in result.get('networkAclSet', []):
            acls.setdefault(acl['networkAclId'], acl)

        for acl_id, acl in sorted(acls.iteritems()):
            self.print_acls(acl)

    def print_acls(self, acl):
        print self.tabify((
            'ACL', acl.get('networkAclId'),
            acl.get('vpcId'),
            acl.get('default')))
        for entry in acl.get('entrySet', []):
            self.print_entry(entry, acl.get('networkAclId'))
        for assoc in acl.get('associationSet', []):
            self.print_association(assoc, acl.get('networkAclId'))

    def print_entry(self, entry, acl_id):
        print self.tabify((
            'RULE', acl_id,
            entry.get('ruleNumber'),
            entry.get('protocol'),
            entry.get('ruleAction'),
            entry.get('cidrBlock'),
            entry.get('portRange'),
            entry.get('egress')))

    def print_association(self, assoc, acl_id):
        print self.tabify((
            'ASSOC', acl_id,
            assoc.get('networkAclAssociationId'),
            assoc.get('networkAclId'),
            assoc.get('subnetId')))
