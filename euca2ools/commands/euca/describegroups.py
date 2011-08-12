# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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

class DescribeGroups(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Shows information about groups.'
    Args = [Param(name='group_name', ptype='string',
                  doc='group to describe',
                  cardinality='+', optional=True)]
    Filters = [Param(name='description', ptype='string',
                     doc='Description of the security group.'),
               Param(name='group-name', ptype='string',
                     doc='Name of the security group.'),
               Param(name='ip-permission.cidr', ptype='string',
                     doc='CIDR range that has been granted the permission.'),
               Param(name='ip-permission.from-port', ptype='string',
                     doc="""Start of port range for the TCP and UDP protocols,
                     or an ICMP type number. An ICMP type number of -1 indicates
                     a wildcard (i.e., any ICMP type number)."""),
               Param(name='ip-permission.group-name', ptype='string',
                     doc="""Name of security group that has been granted
                     the permission."""),
               Param(name='ip-permission.protocol', ptype='string',
                     doc="""IP protocol for the permission.
                     Valid Values: tcp | udp | icmp"""),
               Param(name='ip-permission.to-port', ptype='string',
                     doc="""End of port range for the TCP and UDP protocols,
                     or an ICMP code. An ICMP type number of -1 indicates a
                     wildcard (i.e., any ICMP type number)."""),
               Param(name='ip-permission.user-id', ptype='string',
                     doc="""ID of AWS account that has been granted
                     the permission."""),
               Param(name='owner-id', ptype='string',
                     doc='AWS account ID of the owner of the security group.')]
    
    def display_groups(self, groups):
        for group in groups:
            group_string = '%s\t%s\t%s' % (group.owner_id, group.name,
                    group.description)
            print 'GROUP\t%s' % group_string
            for rule in group.rules:
                permission_string = '%s\t%s\tALLOWS\t%s\t%s\t%s' \
                    % (group.owner_id, group.name, rule.ip_protocol,
                       rule.from_port, rule.to_port)
                for grant in rule.grants:
                    grant_string = '\tFROM'
                    if grant.owner_id or grant.name:
                        if grant.owner_id:
                            grant_string = '\tUSER\t%s' % grant.owner_id
                        if grant.name:
                            grant_string = '\tGRPNAME\t%s' % grant.name
                    else:
                        grant_string += '\tCIDR\t%s' % grant.cidr_ip
                    permission_string += grant_string
                    print 'PERMISSION\t%s' % permission_string
                    
    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_security_groups',
                                     groupnames=self.group_name)

    def main_cli(self):
        groups = self.main()
        self.display_groups(groups)

