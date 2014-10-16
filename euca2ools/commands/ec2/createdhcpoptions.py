# Copyright 2014 Eucalyptus Systems, Inc.
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

import argparse

from requestbuilder import Arg

from euca2ools.commands.ec2 import EC2Request


_DHCP_OPTION_KEYS = ('domain-name-servers', 'domain-name', 'ntp-servers',
                     'netbios-name-servers', 'netbios-node-type')


def _dhcp_option(option_str):
    if '=' not in option_str:
        raise argparse.ArgumentTypeError(
            "value '{0}' must have form KEY=VALUE,VALUE,..."
            .format(option_str))
    key, vals = option_str.split('=', 1)
    if key not in _DHCP_OPTION_KEYS:
        raise argparse.ArgumentTypeError(
            "'{0}' is not a valid DHCP option; choose from {1}"
            .format(key, ', '.join(_DHCP_OPTION_KEYS)))
    return {'Key': key, 'Value': vals.split(',')}


class CreateDhcpOptions(EC2Request):
    DESCRIPTION = 'Create a VPC DHCP option set'
    # EC2 throws 500s when presented with empty DhcpConfigurations.
    ARGS = [Arg('DhcpConfiguration', nargs='+', metavar='KEY=VALUE,[VALUE,...]',
                type=_dhcp_option,
                help='''key and one or more values for a DHCP option (choose
                from {0}) (required)'''.format(', '.join(_DHCP_OPTION_KEYS)))]
    LIST_TAGS = ['dhcpConfigurationSet', 'tagSet', 'valueSet']

    def print_result(self, result):
        self.print_dhcp_options(result.get('dhcpOptions') or {})
