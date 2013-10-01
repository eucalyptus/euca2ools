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


class ReplaceNetworkAclEntry(EucalyptusRequest):
    DESCRIPTION = 'Creates a network acl rule'
    ARGS = [Arg('NetworkAclId', metavar='ACLID',
                help='acl id to create rule in (required)'),
            Arg('-r', '--rule-number', dest='RuleNumber', required=True,
                help='rule number for the acl entry'),
            Arg('-p', '--protocol', dest='Protocol',
                choices=['tcp', 'udp', 'icmp', '-1'], default='-1',
                help='ip protocol number for the rule'),
            Arg('-a', '--rule-action', dest='RuleAction',
                choices=['allow', 'deny'], default='deny',
                help='allow or deny action'),
            Arg('-c', '--cidr-block', dest='CidrBlock', default='0.0.0.0/0',
                help='cidr range e.g. 1.1.1.0/24'),
            Arg('-e', '--egress',
                choices=['true', 'false'], default='false',
                help='egress rule'),
            Arg('-f', '--from-port', dest='PortRange.From', default='0',
                help='start of port range for tcp, udp'),
            Arg('-t', '--to-port', dest='PortRange.To', default='65535',
                help='end of port range for tcp, udp')]

    def print_result(self, result):
        print self.tabify(('ACLID', self.args['NetworkAclId'], result['return']))
