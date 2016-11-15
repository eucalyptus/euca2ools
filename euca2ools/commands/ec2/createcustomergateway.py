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

from requestbuilder import Arg

from euca2ools.commands.ec2 import EC2Request


class CreateCustomerGateway(EC2Request):
    """
    Create a VPN customer gateway

    This is the external side of a VPN connection.  You will also need to
    create a virtual private gateway with euca-create-vpn-gateway(1).
    """

    ARGS = [Arg('-t', '--type', dest='Type', metavar='ipsec.1', required=True,
                choices=('ipsec.1',),
                help='the type of VPN connection to use (required)'),
            Arg('-i', '--ip', dest='IpAddress', metavar='ADDRESS',
                required=True, help='''the new customer gateway's cloud-facing
                IP address (required)'''),
            Arg('-b', '--bgp-asn', dest='BgpAsn', metavar='ASN',
                help="the new customer gateway's BGP AS number")]

    def print_result(self, result):
        self.print_customer_gateway(result.get('customerGateway') or {})
