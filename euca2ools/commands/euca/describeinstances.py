# Software License Agreement (BSD License)
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
import euca2ools.utils

class DescribeInstances(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2010-08-31'
    Description = 'Shows information about instances.'
    Args = [Param(name='instance', ptype='string',
                  cardinality='+', optional=True)]
    Filters = [Param(name='architecture', ptype='string',
                     doc="""Instance architecture.
                     Valid values are i386 | x86_64"""),
               Param(name='availability-zone', ptype='string',
                     doc="Instance's Availability Zone"),
               Param(name='block-device-mapping.attach-time',
                     ptype='datetime',
                     doc="""Attach time for an Amazon EBS volume mapped
                     to the instance"""),
               Param(name='block-device-mapping.delete-on-termination',
                     ptype='boolean',
                     doc="""Whether the Amazon EBS volume is deleted on
                     instance termination."""),
               Param(name='block-device-mapping.device-name', ptype='string',
                     doc="""Device name (e.g., /dev/sdh) for an Amazon EBS volume
                     mapped to the image."""),
               Param(name='block-device-mapping.status', ptype='string',
                     doc="""Status for an Amazon EBS volume mapped to the instance.
                     Valid Values: attaching | attached | detaching | detached"""),
               Param(name='block-device-mapping.volume-id', ptype='string',
                     doc="""ID for an Amazon EBS volume mapped to the instance."""),
               Param(name='client-token', ptype='string',
                     doc="""Idempotency token you provided when you launched
                     the instance."""),
               Param(name='dns-name', ptype='string',
                     doc='Public DNS name of the instance.'),
               Param(name='group-id', ptype='string',
                     doc='A security group the instance is in.'),
               Param(name='hypervisor', ptype='string',
                     doc="""Hypervisor type of the instance.
                     Valid values are ovm | xen."""),
               Param(name='image-id', ptype='string',
                     doc='ID of the imageID used to launch the instance'),
               Param(name='instance-id', ptype='string',
                     doc='ID of the instance'),
               Param(name='instance-lifecycle', ptype='string',
                     doc='Whether this is a Spot Instance.'),
               Param(name='instance-state-code', ptype='integer',
                     doc='Code identifying the state of the instance'),
               Param(name='instance-state-name', ptype='string',
                     doc='State of the instance.'),
               Param(name='instance-type', ptype='string',
                     doc="""Type of the instance."""),
               Param(name='ip-address', ptype='string',
                     doc='Public IP address of the instance.'),
               Param(name='kernel-id', ptype='string',
                     doc='Kernel ID.'),
               Param(name='key-name', ptype='string',
                     doc="""Name of the key pair used when the
                     instance was launched."""),
               Param(name='launch-index', ptype='string',
                     doc="""When launching multiple instances at once,
                     this is the index for the instance in the launch group"""),
               Param(name='launch-time', ptype='string',
                     doc='Time instance was launched'),
               Param(name='monitoring-state', ptype='string',
                     doc='Whether monitoring is enabled for the instance.'),
               Param(name='owner-id', ptype='string',
                     doc='AWS account ID of the image owner.'),
               Param(name='placement-group-name', ptype='string',
                     doc='Name of the placement group the instance is in'),
               Param(name='platform', ptype='string',
                     doc="""Use windows if you have Windows based AMIs;
                     otherwise leave blank."""),
               Param(name='private-dns-name', ptype='string',
                     doc='Private DNS name of the instance.'),
               Param(name='private-ip-address', ptype='string',
                     doc='Private ip address of the instance.'),
               Param(name='product-code', ptype='string',
                     doc='Product code associated with the AMI.'),
               Param(name='ramdisk-id', ptype='string',
                     doc='The ramdisk ID.'),
               Param(name='reason', ptype='string',
                     doc="""Reason for the instance's current state."""),
               Param(name='requestor-id', ptype='string',
                     doc="""ID of the entity that launched the instance
                     on your behalf."""),
               Param(name='reservation-id', ptype='string',
                     doc="""ID of the instance's reservation."""),
               Param(name='root-device-name', ptype='string',
                     doc='Root device name of the AMI (e.g., /dev/sda1).'),
               Param(name='root-device-type', ptype='string',
                     doc="""Root device type the AMI uses.
                     Valid Values: ebs | instance-store."""),
               Param(name='spot-instance-request-id', ptype='string',
                     doc='ID of the Spot Instance request.'),
               Param(name='state-reason-code', ptype='string',
                     doc='Reason code for the state change.'),
               Param(name='state-reason-message', ptype='string',
                     doc='Message for the state change.'),
               Param(name='subnet-id', ptype='string',
                     doc='ID of the subnet the instance is in (VPC).'),
               Param(name='tag-key', ptype='string',
                     doc='Key of a tag assigned to the resource.'),
               Param(name='tag-value', ptype='string',
                     doc='Value of a tag assigned to the resource.'),
               Param(name='tag:key', ptype='string',
                     doc="""Filters the results based on a specific
                     tag/value combination."""),
               Param(name='virtualization-type', ptype='string',
                     doc="""Virtualization type of the instance.
                     Valid values: paravirtual | hvm"""),
               Param(name='vpc-id', ptype='string',
                     doc='ID of the VPC the instance is in.')]
    
    def display_reservations(self, reservations):
        for reservation in reservations:
            instances = []
            instances = reservation.instances
            if len(instances) == 0:
                continue
            reservation_string = '%s\t%s' % (reservation.id,
                    reservation.owner_id)
            group_delim = '\t'
            for group in reservation.groups:
                reservation_string += '%s%s' % (group_delim, group.id)
                group_delim = ', '
            print 'RESERVATION\t%s' % reservation_string
            euca2ools.utils.print_instances(instances)

    def main(self):
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'get_all_instances',
                                     instance_ids=self.instance)

    def main_cli(self):
        reservations = self.main()
        self.display_reservations(reservations)

