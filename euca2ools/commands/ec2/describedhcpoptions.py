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

from requestbuilder import Arg, Filter, GenericTagFilter

from euca2ools.commands.ec2 import EC2Request


class DescribeDhcpOptions(EC2Request):
    DESCRIPTION = 'Show information about VPC DHCP option sets'
    ARGS = [Arg('DhcpOptionsId', metavar='DHCPOPTS', nargs='*',
                help='limit results to specific DHCP option sets')]
    FILTERS = [Filter('dhcp-options-id', help='dhcp option set ID'),
               Filter('key',
                      help='key for one of the options (e.g. domain-name)'),
               Filter('tag-key',
                      help='key of a tag assigned to the DHCP option set'),
               Filter('tag-value',
                      help='value of a tag assigned to the DHCP option set'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('value', help='value for one of the options')]

    LIST_TAGS = ['dhcpConfigurationSet', 'dhcpOptionsSet', 'tagSet', 'valueSet']

    def print_result(self, result):
        for dopt in result.get('dhcpOptionsSet', []):
            self.print_dhcp_options(dopt)
