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

class ReplaceNetworkAclEntry(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = """Replaces an entry (a rule) in a network ACL
                      with the specified rule number"""

    Options = [Param(name='rule_no', short_name='r', ptype='string',
                     optional=False, long_name='rule-num',
                     doc='Rule number to identify order of rules'),
               Param(name='protocol', short_name='p', ptype='string',
                     optional=False, long_name='protocol',
                     doc='Protocol for the rule. Valid values: tcp|udp|icmp|any'),
               Param(name='action', short_name='a', ptype='string',
                     optional=False, long_name='action',
                     doc='Pass or Deny the specified traffic. Valid values: pass|deny'),
               Param(name='network', short_name='n', ptype='string',
                     optional=False, long_name='network',
                     doc='CIDR range for the rule. e.g. x.y.z.w/s'),
               Param(name='direction', short_name='d', ptype='string',
                     optional=True, long_name = 'direction',
                     doc='Direction: ingress|egress'),
               Param(name='fromport', short_name='f', ptype='string',
                     optional=True, long_name='from-port',
                     doc='start of port range for tcp, udp'),
               Param(name='toport', short_name='t', ptype='string',
                     optional=True, long_name='to-port',
                     doc='end of port range for tcp, udp')]

    Args = [Param(name='acl_id',  ptype='string', optional=False,
                  cardinality=1, doc='ID of the acl to replace a rule')]

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'replace_network_acl_entry', acl_id=self.acl_id,
                                            rule_no=self.rule_no, protocol=self.protocol,
                                            action=self.action, network=self.network,
                                            direction=self.direction, fromport=self.fromport,
                                            toport=self.toport)

    def main_cli(self):
        status = self.main()
        if status:
            print status
        else:
            self.error_exit()
