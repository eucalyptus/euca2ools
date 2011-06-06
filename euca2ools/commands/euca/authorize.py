# Software License Agreement (BSD License)
#
# Copyright (c) 20092011, Eucalyptus Systems, Inc.
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
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

import euca2ools.commands.eucacommand
from boto.roboto.param import Param

class Authorize(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Authorize a rule for a security group.'
    Options = [Param(name='protocol', short_name='P', long_name='protocol',
                     optional=True, ptype='string', default='tcp',
                     doc='Protocol ("tcp" "udp" or "icmp").'),
               Param(name='port_range', short_name='p', long_name='port-range',
                     optional=True, ptype='string',
                     doc='Range of ports for the rule (specified as "from-to").'),
               Param(name='icmp_type_code',
                     short_name='t', long_name='icmp-type-code',
                     optional=True, ptype='string',
                     doc='ICMP type and code specified as "type:code"'),
               Param(name='source_group',
                     short_name='o', long_name='source-group',
                     optional=True, ptype='string',
                     doc="""Group from which traffic is authorized
                     by the rule."""),
               Param(name='source_group_user',
                     short_name='u', long_name='source-group-user',
                     optional=True, ptype='string',
                     doc='User ID for the source group.'),
               Param(name='source_subnet',
                     short_name='s', long_name='source-subnet',
                     optional=True, ptype='string', default='0.0.0.0/0',
                     doc="""The source subnet for the rule.
                     Defaults to 0.0.0.0/0.""")]
               
    Args = [Param(name='group_name', ptype='string',
                  doc='Name of the group to add the rule to.',
                  cardinality=1, optional=False)]

    def main(self):
        self.from_port = None
        self.to_port = None
        if self.port_range:
            ports = self.port_range.split('-')
            try:
                if len(ports) > 1:
                    self.from_port = int(ports[0])
                    self.to_port = int(ports[1])
                else:
                    self.from_port = self.to_port = int(ports[0])
            except ValueError:
                self.display_error_and_exit('port must be an integer.')
        if self.icmp_type_code:
            code_parts = self.icmp_type_code.split(':')
            if len(code_parts) > 1:
                try:
                    self.from_port = int(code_parts[0])
                    self.to_port = int(code_parts[1])
                except ValueError:
                    self.display_error_and_exit('port must be an integer.')
        
        conn = self.make_connection_cli()
        return self.make_request_cli(conn,
                                     'authorize_security_group_deprecated',
                                     group_name=self.group_name,
                                     src_security_group_name=self.source_group,
                                     src_security_group_owner_id=self.source_group_user,
                                     ip_protocol=self.protocol,
                                     from_port=self.from_port,
                                     to_port=self.to_port,
                                     cidr_ip=self.source_subnet)

    def main_cli(self):
        status = self.main()
        if status:
            print 'GROUP\t%s' % self.group_name
            permission_string = 'PERMISSION\t%s\tALLOWS' % self.group_name
            if self.protocol:
                permission_string += '\t%s' % self.protocol
            if self.from_port:
                permission_string += '\t%s' % self.from_port
            if self.to_port:
                permission_string += '\t%s' % self.to_port
            if self.source_group_user:
                permission_string += '\tUSER\t%s' \
                    % self.source_group_user
            if self.source_group:
                permission_string += '\tGRPNAME\t%s' % self.source_group
            if self.source_subnet:
                permission_string += '\tFROM\tCIDR\t%s' % self.source_subnet
            print permission_string
