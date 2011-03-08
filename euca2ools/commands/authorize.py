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

import eucacommand
from boto.roboto.param import Param

class Authorize(eucacommand.EucaCommand):

    Description = 'Authorize a rule for a security group.'
    Options = [Param(name='protocol', short_name='P', long_name='protocol',
                     optional=True, ptype='string',
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
                     optional=True, ptype='string',
                     doc="""The source subnet for the rule.
                     Defaults to 0.0.0.0/0.""")]
               
    Args = [Param(name='group_name', ptype='string',
                  doc='Name of the group to add the rule to.',
                  cardinality=1, optional=False)]

    def main(self):
        protocol = self.options.get('protocol', 'tcp')
        from_port = None
        to_port = None
        port_range = self.options.get('port_range', None)
        if port_range:
            ports = port_range.split('-')
            if len(ports) > 1:
                from_port = int(ports[0])
                to_port = int(ports[1])
            else:
                from_port = to_port = int(ports[0])
        icmp_type_code = self.options.get('icmp_type_code', None)
        if icmp_type_code:
            code_parts = value.split(':')
            if len(code_parts) > 1:
                try:
                    from_port = int(code_parts[0])
                    to_port = int(code_parts[1])
                except ValueError:
                    self.display_error_and_exit('port must be an integer.')
        
        source_group = self.options.get('source_group', None)
        source_group_user = self.options.get('source_group_user', None)
        cidr_ip = self.options.get('source_subnet', '0.0.0.0/0')
        
        euca_conn = self.make_connection_cli()
        return_code = self.make_request_cli(euca_conn,
                                            'authorize_security_group',
                                            group_name=group_name,
                                            src_security_group_name=source_group_name,
                                            src_security_group_owner_id=source_group_owner_id,
                                            ip_protocol=protocol,
                                            from_port=from_port,
                                            to_port=to_port,
                                            cidr_ip=cidr_ip)
        if return_code:
            print 'GROUP\t%s' % group_name
            permission_string = 'PERMISSION\t%s\tALLOWS' % group_name
            if protocol:
                permission_string += '\t%s' % protocol
            if from_port:
                permission_string += '\t%s' % from_port
            if to_port:
                permission_string += '\t%s' % to_port
            if source_group_owner_id:
                permission_string += '\tUSER\t%s' \
                    % source_group_owner_id
            if source_group_name:
                permission_string += '\tGRPNAME\t%s' % source_group_name
            if cidr_ip:
                permission_string += '\tFROM\tCIDR\t%s' % cidr_ip
            print permission_string
