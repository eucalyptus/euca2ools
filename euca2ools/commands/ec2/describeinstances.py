# Copyright 2009-2014 Eucalyptus Systems, Inc.
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

from euca2ools.commands.ec2 import EC2Request
from requestbuilder import Arg, Filter, GenericTagFilter


class DescribeInstances(EC2Request):
    DESCRIPTION = 'Show information about instances'
    ARGS = [Arg('InstanceId', metavar='INSTANCE', nargs='*',
                help='limit results to specific instances')]
    FILTERS = [Filter('architecture', help='CPU architecture'),
               Filter('association.allocation-id',
                      help='''[VPC only] allocation ID bound to a network
                      interface's elastic IP address'''),
               Filter('association.association-id', help='''[VPC only]
                      association ID returned when an elastic IP was associated
                      with a network interface'''),
               Filter('association.ip-owner-id',
                      help='''[VPC only] ID of the owner of the elastic IP
                      address associated with a network interface'''),
               Filter('association.public-ip', help='''[VPC only] address of
                      the elastic IP address bound to a network interface'''),
               Filter('availability-zone'),
               Filter('block-device-mapping.attach-time',
                      help='volume attachment time'),
               Filter('block-device-mapping.delete-on-termination', type=bool,
                      help='''whether a volume is deleted upon instance
                      termination'''),
               Filter('block-device-mapping.device-name',
                      help='volume device name (e.g. /dev/sdf)'),
               Filter('block-device-mapping.status', help='volume status'),
               Filter('block-device-mapping.volume-id', help='volume ID'),
               Filter('client-token',
                      help='idempotency token provided at instance run time'),
               Filter('dns-name', help='public DNS name'),
               # EC2's documentation for "group-id" refers VPC users to
               # "instance.group-id", while their documentation for the latter
               # refers them to the former.  Consequently, I'm not going to
               # document a difference for either.  They both seem to work for
               # non-VPC instances.
               Filter('group-id', help='security group ID'),
               Filter('group-name', help='security group name'),
               Filter('hypervisor', help='hypervisor type'),
               Filter('image-id', help='machine image ID'),
               Filter('instance.group-id', help='security group ID'),
               Filter('instance.group-name', help='security group name'),
               Filter('instance-id'),
               Filter('instance-lifecycle',
                      help='whether this is a spot instance'),
               Filter('instance-state-code', type=int,
                      help='numeric code identifying instance state'),
               Filter('instance-state-name', help='instance state'),
               Filter('instance-type'),
               Filter('ip-address', help='public IP address'),
               Filter('kernel-id', help='kernel image ID'),
               Filter('key-name',
                      help='key pair name provided at instance launch time'),
               Filter('launch-index',
                      help='launch index within a reservation'),
               Filter('launch-time', help='instance launch time'),
               Filter('monitoring-state',
                      help='monitoring state ("enabled" or "disabled")'),
               Filter('network-interface.addresses.association.ip-owner-id',
                      help='''[VPC only] ID of the owner of the private IP
                      address associated with a network interface'''),
               Filter('network-interface.addresses.association.public-ip',
                      help='''[VPC only] ID of the association of an elastic IP
                      address with a network interface'''),
               Filter('network-interface.addresses.primary',
                      help='''[VPC only] whether the IP address of the VPC
                      network interface is the primary private IP address
                      ("true" or "false")'''),
               Filter('network-interface.addresses.private-ip-address',
                      help='''[VPC only] network interface's private IP
                      address'''),
               Filter('network-interface.attachment.device-index', type=int,
                      help='''[VPC only] device index to which a network
                      interface is attached'''),
               Filter('network-interface.attachment.attach-time',
                      help='''[VPC only] time a network interface was attached
                      to an instance'''),
               Filter('network-interface.attachment.attachment-id',
                      help='''[VPC only] ID of a network interface's
                      attachment'''),
               Filter('network-interface.attachment.delete-on-termination',
                      help='''[VPC only] whether a network interface attachment
                      is deleted when an instance is terminated ("true" or
                      "false")'''),
               Filter('network-interface.attachment.instance-owner-id',
                      help='''[VPC only] ID of the instance to which a network
                      interface is attached'''),
               Filter('network-interface.attachment.status',
                      help="[VPC only] network interface's attachment status"),
               Filter('network-interface.availability-zone',
                      help="[VPC only] network interface's availability zone"),
               Filter('network-interface.description',
                      help='[VPC only] description of a network interface'),
               Filter('network-interface.group-id',
                      help="[VPC only] network interface's security group ID"),
               Filter('network-interface.group-name', help='''[VPC only]
                      network interface's security group name'''),
               Filter('network-interface.mac-address',
                      help="[VPC only] network interface's hardware address"),
               Filter('network-interface.network-interface.id',
                      help='[VPC only] ID of a network interface'),
               Filter('network-interface.owner-id',
                      help="[VPC only] ID of a network interface's owner"),
               Filter('network-interface.private-dns-name',
                      help="[VPC only] network interface's private DNS name"),
               Filter('network-interface.requester-id',
                      help="[VPC only] network interface's requester ID"),
               Filter('network-interface.requester-managed',
                      help='''[VPC only] whether the network interface is
                      managed by the service'''),
               Filter('network-interface.source-destination-check',
                      help='''[VPC only] whether source/destination checking is
                      enabled for a network interface ("true" or "false")'''),
               Filter('network-interface.status',
                      help="[VPC only] network interface's status"),
               Filter('network-interface.subnet-id',
                      help="[VPC only] ID of a network interface's subnet"),
               Filter('network-interface.vpc-id',
                      help="[VPC only] ID of a network interface's VPC"),
               Filter('owner-id', help="instance owner's account ID"),
               Filter('placement-group-name'),
               Filter('platform', help='"windows" for Windows instances'),
               Filter('private-dns-name'),
               Filter('private-ip-address'),
               Filter('product-code'),
               Filter('product-code.type',
                      help='type of product code ("devpay" or "marketplace")'),
               Filter('ramdisk-id', help='ramdisk image ID'),
               Filter('reason',
                      help="reason for the instance's current state"),
               Filter('requestor-id',
                      help='ID of the entity that launched an instance'),
               Filter('reservation-id'),
               Filter('root-device-name',
                      help='root device name (e.g. /dev/sda1)'),
               Filter('root-device-type',
                      help='root device type ("ebs" or "instance-store")'),
               Filter('spot-instance-request-id'),
               Filter('state-reason-code',
                      help='reason code for the most recent state change'),
               Filter('state-reason-message',
                      help='message describing the most recent state change'),
               Filter('subnet-id',
                      help='[VPC only] ID of the subnet the instance is in'),
               Filter('tag-key',
                      help='name of any tag assigned to the instance'),
               Filter('tag-value',
                      help='value of any tag assigned to the instance'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('virtualization-type'),
               Filter('vpc-id',
                      help='[VPC only] ID of the VPC the instance is in')]
    LIST_TAGS = ['reservationSet', 'instancesSet', 'groupSet', 'tagSet',
                 'blockDeviceMapping', 'productCodes', 'networkInterfaceSet',
                 'privateIpAddressesSet']

    def print_result(self, result):
        for reservation in result.get('reservationSet'):
            self.print_reservation(reservation)
