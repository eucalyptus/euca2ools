# Copyright 2013-2014 Eucalyptus Systems, Inc.
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


class DescribeNetworkAcls(EC2Request):
    DESCRIPTION = 'Describe one or more network ACLs'
    ARGS = [Arg('NetworkAclId', metavar='NACL', nargs='*',
                help='limit results to one or more network ACLs')]
    FILTERS = [Filter('association.association-id',
                      help='ID of an association ID for a network ACL'),
               Filter('association.network-acl-id', help='''ID of the
                      network ACL involved in an association'''),
               Filter('association.subnet-id',
                      help='ID of the subnet involved in an association'),
               Filter('default', choices=('true', 'false'), help='''whether
                      the network ACL is the default for its VPC'''),
               Filter('entry.cidr', help='CIDR range for a network ACL entry'),
               Filter('entry.egress', choices=('true', 'false'),
                      help='whether an entry applies to egress traffic'),
               Filter('entry.icmp.code', type=int,
                      help='ICMP code for a network ACL entry'),
               Filter('entry.icmp.type', type=int,
                      help='ICMP type for a network ACL entry'),
               Filter('entry.port-range.from', type=int,
                      help='start of the port range for a network ACL entry'),
               Filter('entry.port-range.to', type=int,
                      help='end of the port range for a network ACL entry'),
               Filter('entry.protocol',
                      help='protocol for a network ACL entry'),
               Filter('entry.rule-action', choices=('allow', 'deny'), help='''
                      whether a network ACL entry allows or denies traffic'''),
               Filter('entry.rule-number', type=int,
                      help='rule number of a network ACL entry'),
               Filter('network-acl-id'),
               Filter('tag-key',
                      help='key of a tag assigned to the network ACL'),
               Filter('tag-value',
                      help='value of a tag assigned to the network ACL'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('vpc-id', help="the VPC's ID")]

    LIST_TAGS = ['associationSet', 'entrySet', 'networkAclSet', 'tagSet']

    def print_result(self, result):
        for acl in result.get('networkAclSet') or []:
            self.print_network_acl(acl)
