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
from requestbuilder import Arg, MutuallyExclusiveArgList


class CreateNetworkAclEntry(EucalyptusRequest):
    DESCRIPTION = 'Creates a network acl rule'
    ARGS = [Arg('NetworkAclId', metavar='ACLID',
                help='acl id to create rule in (required)'),
            Arg('-n', '--rule-number', dest='RuleNumber', required=True,
                help='rule number for the acl entry (required)'),
            Arg('-p', '--protocol', dest='Protocol', default='-1',
                help='ip protocol number for the rule'),
            MutuallyExclusiveArgList(True,
                Arg('-a', '--allow', dest='RuleAction', help='allow action'),
                Arg('-d', '--deny', dest='RuleAction', help='deny action')),
            Arg('-r', '--cidr-block', dest='CidrBlock',
                help='cidr range e.g. 1.1.1.0/24 (required)')),
            Arg('-e', '--egress', action='store_true',
                help='egress rule'),
            Arg('-p', '--port-range', dest='portRange', metavar='RANGE',
                route_to=None, help='''range of ports (specified as "from-to")
                or a single port number (required for tcp and udp)'''),

    def print_result(self, result):
        print self.tabify((
            'ENTRY',
            self.args.get('egress'),
            self.args.get('ruleNumber'),
            self.args.get('ruleAction'),
            self.args.get('cidrBlock'),
            self.args.get('protocol'),
            self.args.get('portRange')))
