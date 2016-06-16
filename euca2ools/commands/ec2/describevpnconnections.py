# Copyright (c) 2014-2016 Hewlett Packard Enterprise Development LP
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

import sys

from requestbuilder import Arg, Filter, GenericTagFilter
import six

from euca2ools.commands.ec2 import EC2Request


class DescribeVpnConnections(EC2Request):
    DESCRIPTION = 'Show information about VPN connections'
    ARGS = [Arg('VpnConnectionId', metavar='VPNCONN', nargs='*',
                help='limit results to specific VPN connections'),
            Arg('--format', route_to=None, help='''show connection
                information in a specific format (cisco-ios-isr,
                juniper-junos-j, juniper-screenos-6.1, juniper-screenos-6.2,
                generic, xml, none) (default: none)'''),
            Arg('--stylesheet', route_to=None, help='''format the connection
                information using an XSL stylesheet.  If the value contains
                "{format}" it will be replaced with the format chosen by the
                --format option.  If the value is an HTTP or HTTPS URL it
                will be downloaded as needed.  (default: value of
                "vpn-stylesheet" region option)''')]
    FILTERS = [Filter('bgp-asn', help='''the BGP AS number advertised by the
                      customer gateway router'''),
               Filter('customer-gateway-configuration',
                      help='connection information for the customer gateway'),
               Filter('customer-gateway-id',
                      help='ID of the connected customer gateway'),
               Filter('state', help='''the VPN connection's state (available,
                      deleting, deleted, pending)'''),
               Filter('option.static-routes-only',
                      help='''whether the VPN connection is restricted to
                      static routes instead of using BGP'''),
               Filter('route.destination-cidr-block', help='''the address block
                      corresponding to the subnet used in the data center
                      behind the customer gateway router'''),
               Filter('tag-key',
                      help='key of a tag assigned to the VPN connection'),
               Filter('tag-value',
                      help='value of a tag assigned to the VPN connection'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('type',
                      help='the type of virtual private gateway (ipsec.1)'),
               Filter('vpn-connection-id', help='ID of the VPN connection'),
               Filter('vpn-gateway-id',
                      help='ID of the connected virtual private gateway')]
    LIST_TAGS = ['vpnConnectionSet', 'tagSet']

    def print_result(self, result):
        if self.args.get('format') is None:
            stylesheet = self.args.get('stylesheet')
            show_conn_info = bool(stylesheet)
        elif self.args.get('format') == 'none':
            stylesheet = None
            show_conn_info = False
        elif self.args.get('format') == 'xml':
            stylesheet = None
            show_conn_info = True
        else:
            stylesheet = self.args.get('stylesheet')
            if not stylesheet:
                stylesheet = self.config.get_region_option('vpn-stylesheet')
            if stylesheet:
                stylesheet = stylesheet.format(format=self.args['format'])
            else:
                self.log.warn('current region has no stylesheet')
                msg = ('current region has no XSLT stylesheet to format '
                       'output; connection info will not be shown  (try '
                       'specifying one with "--stylesheet" or using '
                       '"--format xml")')
                six.print_(msg, file=sys.stderr)
            show_conn_info = bool(stylesheet)
        for vpn in result.get('vpnConnectionSet', []):
            self.print_vpn_connection(vpn, show_conn_info=show_conn_info,
                                      stylesheet=stylesheet)
