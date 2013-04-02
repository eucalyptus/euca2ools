# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

from boto.roboto.param import Param
import euca2ools.commands.eucacommand


class DescribeInstanceAttribute(euca2ools.commands.eucacommand.EucaCommand):
    Description = ("Show one of an instance's attributes.\n\n"
                   "Note that exactly one attribute may be shown at a time.")
    Options = [Param(name='instanceType', short_name='t',
                     long_name='instance-type', optional=True,
                     ptype='boolean', doc="show the instance's type"),
               Param(name='kernel', long_name='kernel', optional=True,
                     ptype='boolean', doc="show the instance's kernel ID"),
               Param(name='ramdisk', long_name='ramdisk', optional=True,
                     ptype='boolean', doc="show the instance's ramdisk ID"),
               Param(name='userData', long_name='user-data', optional=True,
                     ptype='boolean',
                     doc='show any user-data supplied to the instance'),
               Param(name='disableApiTermination',
                     long_name='disable-api-termination', optional=True,
                     ptype='boolean', doc=('whether the instance can be '
                     'terminated using euca-terminate-instances')),
               Param(name='instanceInitiatedShutdownBehavior',
                     long_name='instance-initiated-shutdown-behavior',
                     optional=True, ptype='boolean', doc=('whether the '
                     'instance will stop or terminate when shut down')),
               Param(name='rootDeviceName', long_name='root-device-name',
                     optional=True, ptype='boolean',
                     doc="name of the instance's root device volume"),
               Param(name='blockDeviceMapping', short_name='b',
                     long_name='block-device-mapping', optional=True,
                     ptype='boolean', doc='block device mappings'),
               Param(name='sourceDestCheck', long_name='source-dest-check',
                     optional=True, ptype='boolean',
                     doc=('whether a VPC instance has source/destination '
                     'checking of its network traffic enabled')),
               Param(name='groupSet', short_name='g', long_name='group-id',
                     optional=True, ptype='boolean',
                     doc='the security groups the instance belongs to'),
               Param(name='productCodes', short_name='p',
                     long_name='product-code', optional=True, ptype='boolean',
                     doc='product codes associated with the instance'),
               Param(name='ebsOptimized', long_name='ebs-optimized',
                     optional=True, ptype='boolean',
                     doc='whether the instance is optimized for EBS I/O')]
    Args = [Param(name='instance_id', optional=False, ptype='string',
                  cardinality=1, doc='ID of the instance to describe')]

    def main(self):
        # Small bug:  when more than one is requested we arbitrarily pick one
        for attr_name in [opt.name for opt in self.Options]:
            if getattr(self, attr_name, None):
                conn = self.make_connection_cli()
                result = self.make_request_cli(conn, 'get_instance_attribute',
                                               instance_id=self.instance_id,
                                               attribute=attr_name)
                return (attr_name, result)
        self.display_error_and_exit('error: an attribute must be specified')

    def print_result(self, result):
        attr_name, value = result

        # Deal with complex data first
        if attr_name == 'blockDeviceMapping':
            for device, mapping in value['blockDeviceMapping'].iteritems():
                print '\t'.join(('BLOCKDEVICE', device, mapping.volume_id,
                                 mapping.attach_time,
                                 str(mapping.delete_on_termination).lower()))
            # The EC2 tools have a couple more fields that I haven't been
            # able to identify.  If you figure out what they are, please send
            # a patch.
        elif attr_name == 'groupSet':
            ## TODO:  test this (EC2 doesn't seem to return any results)
            group_ids = [getattr(group, 'id', group.name) for group in
                         value.get('groupSet', [])]
            print '\t'.join((attr_name, self.instance_id,
                             ', '.join(group_ids)))
        elif attr_name == 'productCodes':
            ## TODO:  test this (I don't have anything I can test it with)
            print '\t'.join((attr_name, self.instance_id,
                             ', '.join(value.get('productCodes', []))))
        else:
            print '\t'.join((attr_name, self.instance_id, value[attr_name]))

    def main_cli(self):
        result = self.main()
        self.print_result(result)
