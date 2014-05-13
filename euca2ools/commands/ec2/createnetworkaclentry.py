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

import socket

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.ec2 import EC2Request, parse_ports


class CreateNetworkAclEntry(EC2Request):
    DESCRIPTION = 'Create a network ACL entry'
    ARGS = [Arg('NetworkAclId', metavar='NACL',
                help='ID of the network ACL to add the entry to (required)'),
            Arg('-n', '--rule-number', dest='RuleNumber', metavar='INT',
                required=True, type=int,
                help='rule number for the new entry (required)'),
            MutuallyExclusiveArgList(
                Arg('--allow', dest='RuleAction', action='store_const',
                    const='allow',
                    help='make the new entry allow the traffic it matches'),
                Arg('--deny', dest='RuleAction', action='store_const',
                    const='deny',
                    help='make the new entry block the traffic it matches'))
            .required(),
            Arg('-r', '--cidr', dest='CidrBlock', metavar='CIDR',
                required=True,
                help='CIDR address range the entry should affect (required)'),
            Arg('-P', '--protocol', dest='Protocol', default='-1',
                help='protocol the entry should apply to (default: all)'),
            Arg('--egress', dest='Egress', action='store_true',
                help='''make the entry affect outgoing (egress) network
                traffic (default: affect incoming (ingress) traffic)'''),
            Arg('-p', '--port-range', dest='port_range', metavar='RANGE',
                route_to=None, help='''range of ports (specified as "from-to")
                or a single port number (required for tcp and udp)'''),
            Arg('-t', '--icmp-type-code', dest='icmp_type_code',
                metavar='TYPE:CODE', route_to=None, help='''ICMP type and
                code (specified as "type:code") (required for icmp)''')]

    def process_cli_args(self):
        self.process_port_cli_args()

    def configure(self):
        EC2Request.configure(self)
        if not self.params.get('Egress'):
            self.params['Egress'] = False
        proto = self.args.get('Protocol') or -1
        try:
            self.params['Protocol'] = int(proto)
        except ValueError:
            if proto.lower() == 'all':
                self.params['Protocol'] = -1
            else:
                try:
                    self.params['Protocol'] = socket.getprotobyname(proto)
                except socket.error:
                    raise ArgumentError('argument -n/--rule-number: unknown '
                                        'protocol "{0}"'.format(proto))
        from_port, to_port = parse_ports(proto, self.args.get('port_range'),
                                         self.args.get('icmp_type_code'))
        if self.params['Protocol'] == 1:  # ICMP
            self.params['Icmp.Type'] = from_port
            self.params['Icmp.Code'] = to_port
        else:
            self.params['PortRange.From'] = from_port
            self.params['PortRange.To'] = to_port

    def print_result(self, result):
        if self.args.get('Egress'):
            direction = 'egress'
        else:
            direction = 'ingress'
        protocol = self.params['Protocol']
        port_map = {-1: 'all', 1: 'icmp', 6: 'tcp', 17: 'udp', 132: 'sctp'}
        try:
            protocol = port_map.get(int(protocol), int(protocol))
        except ValueError:
            pass

        print self.tabify((
            'ENTRY', direction, self.params.get('RuleNumber'),
            self.params.get('RuleAction'), self.params.get('CidrBlock'),
            protocol,
            self.params.get('Icmp.Type') or self.params.get('PortRange.From'),
            self.params.get('Icmp.Code') or self.params.get('PortRange.To')))
