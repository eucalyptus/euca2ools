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

class DescribeNetworkAcl(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-07-15'
    Description = """Describe a network ACL"""

    Args = [Param(name='acl_id', ptype='string', optional=True, cardinality=1,
                  doc='Id of acl to display')]

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'get_all_network_acl', acl_id=self.acl_id)

    def main_cli(self):
        acls = self.main()
        if acls:
            for acl in acls:
                default=''
                if acl.default == 'true':
                    default = '(def)'
                print "%-16s" % ('AclId')
                print "%-16s" % ('-----')
                print "%s%s\n%s" % (acl.id, default, acl.vpc_id)

                print "%-16s%-8s%-8s%-8s%-8s%-6s%-8s%-24s" % ('', 'Rule', 'Dir', 'Action', 'Proto', 'Port', 'Range', 'Cidr')
                print "%-16s%-8s%-8s%-8s%-8s%-6s%-8s%-24s" % ('', '----', '---', '------', '-----', '----', '-----', '----')
                for rule in acl.network_acl_entries:
                    direction = 'ingress'
                    if rule.egress == 'true':
                        direction = 'egress'
                    print "%-16s%-8s%-8s%-8s%-8s%-6s%-8s%-24s" % ('', rule.rule_number, direction,
                           rule.rule_action, rule.protocol, rule.port_range.from_port, 
                           rule.port_range.to_port, rule.cidr_block)

                print "\n"
                print "%-16s%-20s%-20s%-20s" % ('', 'Assocation', 'SubnetId', 'RouteTableId')
                print "%-16s%-20s%-20s%-20s" % ('', '----------', '--------', '------------')
                for assoc in acl.associations:
                    print "%-16s%-20s%-20s%-20s" % ('', assoc.id, assoc.subnet_id, assoc.route_table_id)
        else:
            self.error_exit()
