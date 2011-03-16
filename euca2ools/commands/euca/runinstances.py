# Software License Agreement (BSD License)
#
# Copyright (c) 20092011, Eucalyptus Systems, Inc.
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

class RunInstances(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Starts instances.'
    Options = [Param(name='count', short_name='n', long_name='instance-count',
                     optional=True, ptype='string',
                     doc='Number of instances to run.'),
               Param(name='group_name', short_name='g', long_name='group',
                     optional=True, ptype='string', cardinality='*',
                     doc='Security group to run the instance in.'),
               Param(name='keyname', short_name='k', long_name='key',
                     optional=True, ptype='string',
                     doc='Name of a keypair.'),
               Param(name='user_data', short_name='d', long_name='user-data',
                     optional=True, ptype='file',
                     doc='User data to pass to the instance.'),
               Param(name='user_data_file',
                     short_name='f', long_name='user-data-file',
                     optional=True, ptype='file',
                     doc='File containing user data to pass to the instance.'),
               Param(name='addressing', long_name='addressing',
                     optional=True, ptype='string',
                     doc='Deprecated.'),
               Param(name='instance_type',
                     short_name='t', long_name='instance-type',
                     optional=True, ptype='string',
                     doc='VM Image type to run the instance as.'),
               Param(name='kernel', long_name='kernel',
                     optional=True, ptype='string',
                     doc='ID of the kernel to be used.'),
               Param(name='ramdisk', long_name='ramdisk',
                     optional=True, ptype='string',
                     doc='ID of the ramdisk to be used.'),
               Param(name='block_device_mapping',
                     short_name='b', long_name='block-device-mapping',
                     optional=True, ptype='string', cardinality='*',
                     doc="""Block device mapping for the instance(s).
                     Option may be used multiple times"""),
               Param(name='monitor', long_name='monitor',
                     optional=True, ptype='boolean',
                     doc='Enable monitoring for the instance.'),
               Param(name='subnet', short_name='s', long_name='subnet',
                     optional=True, ptype='string',
                     doc='Amazon VPC subnet ID for the instance.'),
               Param(name='zone', short_name='z', long_name='availability-zone',
                     optional=True, ptype='string',
                     doc='availability zone to run the instance in')]
    Args = [Param(name='image_id', ptype='string',
                  optional=False,
                  doc='ID of the image to run.')]

    def display_reservations(self, reservation):
        reservation_string = '%s\t%s' % (reservation.id,
                reservation.owner_id)
        group_delim = '\t'
        for group in reservation.groups:
            reservation_string += '%s%s' % (group_delim, group.id)
            group_delim = ', '
        print 'RESERVATION\t%s' % reservation_string
        euca2ools.utils.print_instances(reservation.instances)

    def read_user_data(self, user_data_filename):
        fp = open(user_data_filename)
        user_data = fp.read()
        fp.close()
        return user_data

    def main(self):
        image_id = self.arguments['image_id']
        keyname = self.options.get('keyname', None)
        kernel_id = self.options.get('kernel', None)
        ramdisk_id = self.options.get('ramdisk', None)
        count = self.options.get('count', '1')
        t = count.split('-')
        try:
            if len(t) > 1:
                min_count = int(t[0])
                max_count = int(t[1])
            else:
                min_count = max_count = int(t[0])
        except ValueError:
            msg = 'Invalid value for --instance-count: %s' % count
            self.display_error_and_exit(msg)
                
        instance_type = self.options.get('instance_type', 'm1.small')
        group_names = self.options.get('group', [])
        user_data = self.options.get('user_data', None)
        user_data_file = self.options.get('user_data_file', None)
        addressing_type = self.options.get('addressing', None)
        zone = self.options.get('zone', None)
        block_device_map = self.options.get('block_device_mappings', [])
        monitor = self.options.get('monitor', False)
        subnet_id = self.options.get('subnet', None)

        if not user_data:
            if user_data_file:
                user_data = self.read_user_data(user_data_file)

        if block_device_map:
            block_device_map = self.parse_block_device_args(block_device_map)
        euca_conn = self.make_connection_cli()
        reservation = self.make_request_cli(euca_conn,
                                            'run_instances',
                                            image_id=image_id,
                                            min_count=min_count,
                                            max_count=max_count,
                                            key_name=keyname,
                                            security_groups=group_names,
                                            user_data=user_data,
                                            addressing_type=addressing_type,
                                            instance_type=instance_type,
                                            placement=zone,
                                            kernel_id=kernel_id,
                                            ramdisk_id=ramdisk_id,
                                            block_device_map=block_device_map,
                                            monitoring_enabled=monitor,
                                            subnet_id=subnet_id)
        self.display_reservations(reservation)

