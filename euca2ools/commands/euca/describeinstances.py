# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2012, Eucalyptus Systems, Inc.
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

from requestbuilder import Arg, Filter, GenericTagFilter
from . import EucalyptusRequest

class DescribeInstances(EucalyptusRequest):
    API_VERSION = '2010-08-31'
    DESCRIPTION = 'Show information about instances'
    ARGS = [Arg('InstanceId', metavar='INSTANCE', nargs='*',
                help='Limit results to one or more instances')]
    FILTERS = [Filter('architecture', help='CPU architecture'),
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
               Filter('group-id', help='security group membership'),
               Filter('hypervisor', help='hypervisor type'),
               Filter('image-id', help='machine image ID'),
               Filter('instance-id'),
               Filter('instance-lifecycle', choices=['spot'],
                      help='whether this is a spot instance'),
               Filter('instance-state-code', type=int,
                      help='numeric code identifying instance state'),
               Filter('instance-state-name', help='instance state'),
               Filter('instance-type',),
               Filter('ip-address', help='public IP address'),
               Filter('kernel-id', help='kernel image ID'),
               Filter('key-name',
                      help='key pair name provided at instance launch time'),
               Filter('launch-index', help='launch index within a reservation'),
               Filter('launch-time', help='instance launch time'),
               Filter('monitoring-state', help='whether monitoring is enabled'),
               Filter('owner-id', help='instance owner\'s account ID'),
               Filter('placement-group-name'),
               Filter('platform', choices=['windows'],
                      help='whether this is a Windows instance'),
               Filter('private-dns-name'),
               Filter('private-ip-address'),
               Filter('product-code'),
               Filter('ramdisk-id', help='ramdisk image ID'),
               Filter('reason', help='reason for the more recent state change'),
               Filter('requestor-id',
                      help='ID of the entity that launched an instance'),
               Filter('reservation-id'),
               Filter('root-device-name',
                      help='root device name (e.g. /dev/sda1)'),
               Filter('root-device-type', choices=['ebs', 'instance-store'],
                      help='root device type (ebs or instance-store)'),
               Filter('spot-instance-request-id'),
               Filter('state-reason-code',
                      help='reason code for the most recent state change'),
               Filter('state-reason-message',
                      help='message for the most recent state change'),
               Filter('subnet-id',
                      help='ID of the VPC subnet the instance is in'),
               Filter('tag-key',
                      help='name of any tag assigned to the instance'),
               Filter('tag-value',
                      help='value of any tag assigned to the instance'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter('virtualization-type', choices=['paravirtual', 'hvm']),
               Filter('vpc-id', help='ID of the VPC the instance is in')]
    ListDelims = ['reservationSet', 'instancesSet', 'groupSet', 'tagSet',
                  'blockDeviceMapping', 'productCodes']

    def print_result(self, result):
        for reservation in result.get('reservationSet'):
            self.print_reservation(reservation)
