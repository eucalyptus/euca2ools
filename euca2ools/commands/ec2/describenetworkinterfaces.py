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


class DescribeNetworkInterfaces(EC2Request):
    DESCRIPTION = 'Show information about VPC network interfaces'
    ARGS = [Arg('NetworkInterfaceId', metavar='INTERFACE', nargs='*',
                help='limit results to specific network interfaces')]
    FILTERS = [Filter('addresses.private-ip-addresses',
                      help="the interface's private IP addresses"),
               Filter('addresses.primary', help='''whether the private IP
                      address is the network interface's primary IP address'''),
               Filter('addresses.association.public-ip', help='''association
                      ID for the network interface's elastic IP address'''),
               Filter('addresses.association.owner-id', help='''owner ID of
                      the addresses associated with the network interface'''),
               Filter('association.association-id', help='''association ID of
                      the network interface's IP Address'''),
               Filter('association.allocation-id', help='''allocation ID of the
                      network interface's elastic IP address'''),
               Filter('association.ip-owner-id', help='''owner ID of the
                      network interface's elastic IP address'''),
               Filter('association.public-ip',
                      help="network interface's elastic IP address"),
               Filter('association.public-dns-name',
                      help="network interface's public DNS name"),
               Filter('attachment.attachment-id',
                      help="ID of the network interface's attachment"),
               Filter('attachment.instance-id', help='''ID of the instance the
                      network interface is attached to'''),
               Filter('attachment.instance-owner-id', help='''owner ID of the
                      instance the network interface is attached to'''),
               Filter('attachment.device-index', help='''device index to which
                      the network interface is attached'''),
               Filter('attachment.status', help='''attachment status
                      (attaching, attached, detaching, detached)'''),
               Filter('attachment.attach.time',
                      help='time the network interface was attached'),
               Filter('attachment.delete-on-termination',
                      help='''whether the attachment will be deleted when the
                      associated instance is terminated'''),
               Filter('availability-zone', help='''availability zone in which
                      the network interface resides'''),
               Filter('description', help="network interface's description"),
               Filter('group-id', help='''ID of a security group associated
                      with the network interface'''),
               Filter('group-name', help='''name of a security group associated
                      with the network interface'''),
               Filter('mac-address', help='MAC (hardware) address'),
               Filter('network-interface-id',
                      help='ID of the network interface'),
               Filter('owner-id',
                      help="account ID of the network interface's owner"),
               Filter('private-ip-address',
                      help="the network interface's private address(es)"),
               Filter('private-dns-name',
                      help="the network interface's private DNS name"),
               Filter('requester-id', help='''ID of the entity that created
                      the network interface'''),
               Filter('requester-managed', help='''whether the network interface
                      is being managed by one of the cloud's services'''),
               Filter('source-dest-check',
                      help='''whether the network interface's traffic is
                      subject to source/destination address checking'''),
               Filter('status',
                      help="the interface's status (available, in-use)"),
               Filter('subnet-id', help='''ID of the subnet in which the
                      network interface resides'''),
               Filter('tag-key',
                      help='key of a tag assigned to the network interface'),
               Filter('tag-value',
                      help='value of a tag assigned to the network interface'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('vpc-id', help='''ID of the VPC in which the network
                      interface resides''')]

    LIST_TAGS = ['groupSet', 'networkInterfaceSet', 'privateIpAddressesSet',
                 'tagSet']

    def print_result(self, result):
        for nic in result.get('networkInterfaceSet') or []:
            self.print_interface(nic)
