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

class DescribeRouteTables(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = """Describes one or more of your route tables."""

    Args = [Param(name='route_table_id', ptype='string', optional=True,
                  doc='One or more route table IDs. E.g. rtb-123456')]

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'get_all_route_tables',
                                     route_table_ids=self.route_table_id)

    def display_route_tables(self, route_tables=None):
        if route_tables:
            for route_table in route_tables:
                print "%-16s%-8s%-20s%-20s%-20s" % ('RouteTableId', 'Main', 'VpcId', 'AssociationId', 'SubnetId')
                print "%-16s%-8s%-20s%-20s%-20s" % ('------------', '----', '-----', '-------------', '--------')
                rtb_name = route_table.id
                main = 'no'
                printed = False
                for assoc in route_table.associations:
                    if assoc.main:
                        main = 'yes'
                    print "%-16s%-8s%-20s%-20s%-20s" % (rtb_name, main, route_table.vpc_id, assoc.id, assoc.subnet_id)
                    printed = True

                if printed == False:
                    print "%-16s%-8s%-20s" % (rtb_name, main, route_table.vpc_id)
                print "%-16s%-24s%-24s" % ('', 'Prefix', 'NextHop')
                print "%-16s%-24s%-24s" % ('', '------', '-------')
                for route in route_table.routes:
                    print "%-16s%-24s%-24s" % ('', route.destination_cidr_block,
                                              route.gateway_id)


    def main_cli(self):
        route_tables = self.main()
        self.display_route_tables(route_tables)
