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
import os.path

class RunInstances(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Starts instances.'
    Options = [Param(name='count', short_name='n', long_name='instance-count',
                     optional=True, ptype='string', default='1',
                     doc='Number of instances to run.'),
               Param(name='group_name', short_name='g', long_name='group',
                     optional=True, ptype='string', cardinality='*',
                     doc='Security group to run the instance in.'),
               Param(name='keyname', short_name='k', long_name='key',
                     optional=True, ptype='string',
                     doc='Name of a keypair.'),
               Param(name='user_data', short_name='d', long_name='user-data',
                     optional=True, doc='User data to pass to the instance.'),
               Param(name='user_data_force', long_name='user-data-force',
                     optional=True,
                     doc='Just like --user-data, but ignore any checks.'),
               Param(name='user_data_file',
                     short_name='f', long_name='user-data-file',
                     optional=True, ptype='file',
                     doc='File containing user data to pass to the instance.'),
               Param(name='addressing', long_name='addressing',
                     optional=True, ptype='string',
                     doc=('[Eucalyptus extension] Address assignment method.  '
                          'Use "private" to run an instance with no public '
                          'address.')),
               Param(name='instance_type',
                     short_name='t', long_name='instance-type',
                     optional=True, ptype='string', default='m1.small',
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
                     optional=True, ptype='boolean', default=False,
                     doc='Enable monitoring for the instance.'),
               Param(name='subnet', short_name='s', long_name='subnet',
                     optional=True, ptype='string',
                     doc='Amazon VPC subnet ID for the instance.'),
               Param(name='zone', short_name='z', long_name='availability-zone',
                     optional=True, ptype='string',
                     doc='availability zone to run the instance in'),
               Param(name='instance_initiated_shutdown_behavior',
                     long_name='instance-initiated-shutdown-behavior',
                     optional=True, ptype='string',
                     doc='Whether to "stop" (default) or "terminate" instance when it is shut down')]
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
        t = self.count.split('-')
        try:
            if len(t) > 1:
                min_count = int(t[0])
                max_count = int(t[1])
            else:
                min_count = max_count = int(t[0])
        except ValueError:
            msg = 'Invalid value for --instance-count: %s' % count
            self.display_error_and_exit(msg)
                
        if self.user_data and os.path.isfile(self.user_data):
            msg = ('string provided as user-data [%s] is a file.\nTry %s or %s'
                    % (self.user_data, '--user-data-file', '--user-data-force'))
            self.display_error_and_exit(msg)

        if self.user_data_force:
            self.user_data = self.user_data_force

        if not self.user_data:
            if self.user_data_file:
                self.user_data = self.read_user_data(self.user_data_file)

        if self.block_device_mapping:
            self.block_device_mapping = self.parse_block_device_args(self.block_device_mapping)
        conn = self.make_connection_cli()
        return self.make_request_cli(conn, 'run_instances',
                                     image_id=self.image_id,
                                     min_count=min_count,
                                     max_count=max_count,
                                     key_name=self.keyname,
                                     security_groups=self.group_name,
                                     user_data=self.user_data,
                                     addressing_type=self.addressing,
                                     instance_type=self.instance_type,
                                     placement=self.zone,
                                     kernel_id=self.kernel,
                                     ramdisk_id=self.ramdisk,
                                     block_device_map=self.block_device_mapping,
                                     monitoring_enabled=self.monitor,
                                     subnet_id=self.subnet,
                                     instance_initiated_shutdown_behavior=self.instance_initiated_shutdown_behavior)

    def main_cli(self):
        reservation = self.main()
        self.display_reservations(reservation)

