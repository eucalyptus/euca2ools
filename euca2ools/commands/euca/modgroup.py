# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from requestbuilder import Arg, MutuallyExclusiveArgList
import sys
from . import EucalyptusRequest

class ModifySecurityGroupRequest(EucalyptusRequest):
    '''
    The basis for security group-editing commands
    '''

    ARGS = [Arg('GroupName', metavar='GROUP',
                help='name of the security group to modify'),
            Arg('-P', '--protocol', dest='IpPermissions.1.IpProtocol',
                choices=['tcp', 'udp', 'icmp', '6', '17', '1'], default='tcp',
                help='protocol to affect (default: tcp)'),
            Arg('-p', '--port-range', dest='port_range', route_to=None,
                help='''range of ports (specified as "from-to") or a single
                        port'''),
                # ^ required for tcp and udp
            Arg('-t', '--icmp-type-code', dest='icmp_type_code',
                metavar='TYPE:CODE', route_to=None,
                help='ICMP type and code (specified as "type:code")'),
                # ^ required for icmp
            MutuallyExclusiveArgList(
                Arg('-s', '--cidr', metavar='CIDR',
                    dest='IpPermissions.1.IpRanges.1.CidrIp',
                    help='''IP range (default: 0.0.0.0/0)'''),
                    # ^ default is added by main()
                Arg('-o', metavar='GROUP',
                    dest='IpPermissions.1.Groups.1.GroupName',
                    help='''name of a security group with which to authorize
                            network communication''')),
            Arg('-u', metavar='GROUP_USER',
                dest='IpPermissions.1.Groups.1.UserId',
                help='''ID of the account that owns the security group
                        specified with -o''')]
                # ^ required if -o is used

    def configure(self):
        EucalyptusRequest.configure(self)

        from_port = None
        to_port   = None
        protocol = self.args.get('IpPermissions.1.IpProtocol')
        if protocol in ['icmp', '1']:
            if not self.args.get('icmp_type_code'):
                self._cli_parser.error('argument -t/--icmp-type-code is '
                                       'required for ICMP')
            types = self.args['icmp_type_code'].split(':')
            if len(types) == 2:
                try:
                    from_port = int(types[0])
                    to_port   = int(types[1])
                except ValueError:
                    self._cli_parser.error('argument -t/--icmp-type-code: '
                                           'value must have format "1:2"')
            else:
                self._cli_parser.error('argument -t/--icmp-type-code: value '
                                       'must have format "1:2"')
            if from_port < -1 or to_port < -1:
                self._cli_parser.error('argument -t/--icmp-type-code: type, '
                                       'code must be at least -1')

        elif protocol in ['tcp', 'udp', '6', '17']:
            if not self.args.get('port_range'):
                self._cli_parser.error('argument -p/--port-range is required '
                                       'for protocol ' + protocol)
            if ':' in self.args['port_range']:
                # Be extra helpful in the event of this common typo
                self._cli_parser.error('argument -p/--port-range: multi-port '
                        'range must be separated by "-", not ":"')
            if self.args['port_range'].startswith('-'):
                ports = self.args['port_range'][1:].split('-')
                ports[0] = '-' + ports[0]
            else:
                ports = self.args['port_range'].split('-')
            if len(ports) == 2:
                try:
                    from_port = int(ports[0])
                    to_port   = int(ports[1])
                except ValueError:
                    self._cli_parser.error('argument -p/--port-range: '
                            'multi-port value must be comprised of integers')
            elif len(ports) == 1:
                try:
                    from_port = to_port = int(ports[0])
                except ValueError:
                    self._cli_parser.error('argument -p/--port-range: single '
                                           'port value must be an integer')
            else:
                self._cli_parser.error('argument -p/--port-range: value must '
                                       'have format "1" or "1-2"')
            if from_port < -1 or to_port < -1:
                self._cli_parser.error('argument -p/--port-range: port '
                                       'number(s) must be at least -1')

        self.params['IpPermissions.1.FromPort'] = from_port
        self.params['IpPermissions.1.ToPort']   = to_port

        if not self.args.get('IpPermissions.1.IpRanges.1.GroupName'):
            self.args.setdefault('IpPermissions.1.IpRanges.1.CidrIp',
                                 '0.0.0.0/0')
        if (self.args.get('IpPermissions.1.Groups.1.GroupName') and
            not self.args.get('IpPermissions.1.Groups.1.UserId')):
            self._cli_parser.error('argument -u is required when -o is '
                                   'specified')

    def print_result(self, result):
        print self.tabify(['GROUP', self.args.get('GroupName')])
        perm_str = ['PERMISSION', self.args.get('GroupName'), 'ALLOWS',
                    self.args.get('IpPermissions.1.IpProtocol'),
                    self.args.get('IpPermissions.1.FromPort'),
                    self.args.get('IpPermissions.1.ToPort')]
        if self.args.get('IpPermissions.1.Groups.1.UserId'):
            perm_str.append('USER')
            perm_str.append(self.args.get('IpPermissions.1.Groups.1.UserId'))
        if self.args.get('IpPermissions.1.Groups.1.GroupName'):
            perm_str.append('GRPNAME')
            perm_str.append(self.args.get(
                    'IpPermissions.1.Groups.1.GroupName'))
        if self.args.get('IpPermissions.1.IpRanges.1.CidrIp'):
            perm_str.extend(['FROM', 'CIDR'])
            perm_str.append(self.args.get('IpPermissions.1.IpRanges.1.CidrIp'))
        print self.tabify(perm_str)

    def process_cli_args(self):
        # We need to parse out -t and -p *before* argparse can see it because
        # of Python bug 9334, which prevents argparse from recognizing '-1:-1'
        # as an option value and not a (nonexistent) option name.
        def parse_neg_one_value(opt_name):
            if opt_name in sys.argv:
                index = sys.argv.index(opt_name)
                if (index < len(sys.argv) - 1 and
                    sys.argv[index + 1].startswith('-1')):
                    opt_val = sys.argv[index + 1]
                    del sys.argv[index:index + 2]
                    return opt_val
        icmp_type_code = (parse_neg_one_value('-t') or
                          parse_neg_one_value('--icmp-type-code'))
        port_range = (parse_neg_one_value('-p') or
                      parse_neg_one_value('--port-range'))
        EucalyptusRequest._process_cli_args(self)
        if icmp_type_code:
            self.args['icmp_type_code'] = icmp_type_code
        if port_range:
            self.args['port_range'] = port_range
