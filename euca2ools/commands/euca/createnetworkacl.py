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


class CreateNetworkAcl(EucalyptusRequest):
    DESCRIPTION = 'Create ACL for VPC'
    ARGS = [Arg('VpcId', metavar='VPC',
                help='vpc id to create acl (required)')]
    LIST_TAGS = ['entrySet']

    def print_result(self, result):
        acl = result.get('networkAcl')
        print self.tabify((
            'NETWORKACL', acl.get('networkAclId'),
            acl.get('vpcId')))

        for entry in acl.get('entrySet', []):
            self.print_entry(entry, acl.get('networkAclId'))

    def print_entry(self, entry, acl_id):
        direction = 'ingress'
        if entry.get('egress'):
            direction = 'egress'

        print self.tabify((
            'ENTRY', direction,
            entry.get('ruleNumber'),
            entry.get('ruleAction'),
            entry.get('cidrBlock'),
            entry.get('protocol'),
            entry.get('portRange')))
