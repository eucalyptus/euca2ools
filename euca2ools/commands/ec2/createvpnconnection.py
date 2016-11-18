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

from requestbuilder import Arg
import six

from euca2ools.commands.ec2 import EC2Request


class CreateVpnConnection(EC2Request):
    DESCRIPTION = ('Create a VPN connection between a virtual private '
                   'gateway and a customer gateway\n\nYou can optionally '
                   'format the connection information for specific '
                   'devices using the --format or --stylesheet options.  '
                   'If the --stylesheet option is an HTTP or HTTPS URL it '
                   'will be downloaded as needed.')
    ARGS = [Arg('-t', '--type', dest='Type', metavar='ipsec.1', required=True,
                choices=('ipsec.1',),
                help='the type of VPN connection to use (required)'),
            Arg('--customer-gateway', dest='CustomerGatewayId', required=True,
                metavar='CGATEWAY',
                help='ID of the customer gateway to connect (required)'),
            Arg('--vpn-gateway', dest='VpnGatewayId', required=True,
                metavar='VGATEWAY', help='''ID of the virtual private gateway
                to connect (required)'''),
            Arg('--static-routes-only', dest='Options.StaticRoutesOnly',
                action='store_true',
                help='use only static routes instead of BGP'),
            Arg('--format', route_to=None, help='''show connection
                information in a specific format (cisco-ios-isr,
                juniper-junos-j, juniper-screenos-6.1, juniper-screenos-6.2,
                generic, xml, none) (default: xml)'''),
            Arg('--stylesheet', route_to=None, help='''format the connection
                information using an XSL stylesheet.  If the value contains
                "{format}" it will be replaced with the format chosen by the
                --format option.  If the value is an HTTP or HTTPS URL it
                will be downloaded as needed.  (default: value of
                "vpn-stylesheet" region option)''')]

    def print_result(self, result):
        if self.args.get('format') is None:
            # If --stylesheet is used it will be applied.  Otherwise,
            # None will make it print the raw XML, which is what we want.
            stylesheet = self.args.get('stylesheet')
            show_conn_info = True
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
        self.print_vpn_connection(result.get('vpnConnection') or {},
                                  show_conn_info=show_conn_info,
                                  stylesheet=stylesheet)
