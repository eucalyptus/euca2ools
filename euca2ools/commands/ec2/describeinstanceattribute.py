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

import base64

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.ec2 import EC2Request


class DescribeInstanceAttribute(EC2Request):
    DESCRIPTION = ("Show one of an instance's attributes.\n\n"
                   "Note that exactly one attribute may be shown at a time.")
    ARGS = [Arg('InstanceId', metavar='INSTANCE',
                help='ID of the instance to show info for (required)'),
            MutuallyExclusiveArgList(
                Arg('-b', '--block-device-mapping', dest='Attribute',
                    action='store_const', const='blockDeviceMapping',
                    help='show block device mappings'),
                Arg('--disable-api-termination', dest='Attribute',
                    action='store_const', const='disableApiTermination',
                    help='show whether termination is disabled'),
                Arg('--ebs-optimized', dest='Attribute', action='store_const',
                    const='ebsOptimized', help='''show whether the root volume
                    is optimized for EBS I/O'''),
                Arg('-g', '--group-id', dest='Attribute', action='store_const',
                    const='groupSet',
                    help='show the security groups the instance belongs to'),
                Arg('-p', '--product-code', dest='Attribute',
                    action='store_const', const='productCodes',
                    help='show any associated product codes'),
                Arg('--instance-initiated-shutdown-behavior', dest='Attribute',
                    action='store_const',
                    const='instanceInitiatedShutdownBehavior',
                    help='''show whether the instance stops or terminates
                    when shut down'''),
                Arg('-t', '--instance-type', dest='Attribute',
                    action='store_const', const='instanceType',
                    help="show the instance's type"),
                Arg('--kernel', dest='Attribute', action='store_const',
                    const='kernel', help='''show the ID of the kernel image
                    associated with the instance'''),
                Arg('--ramdisk', dest='Attribute', action='store_const',
                    const='ramdisk', help='''show the ID of the ramdisk image
                    associated with the instance'''),
                Arg('--root-device-name', dest='Attribute',
                    action='store_const', const='rootDeviceName',
                    help='''show the name of the instance's root device
                    (e.g. '/dev/sda1')'''),
                Arg('--source-dest-check', dest='Attribute',
                    action='store_const', const='sourceDestCheck',
                    help='''[VPC only] show whether source/destination checking
                    is enabled for the instance'''),
                Arg('--user-data', dest='Attribute', action='store_const',
                    const='userData', help="show the instance's user-data"))
            .required()]
    LIST_TAGS = ['blockDeviceMapping', 'groupSet', 'productCodes']

    def print_result(self, result):
        # Deal with complex data first
        if self.args['Attribute'] == 'blockDeviceMapping':
            for mapping in result.get('blockDeviceMapping', []):
                ebs = mapping.get('ebs', {})
                print self.tabify(('BLOCKDEVICE', mapping.get('deviceName'),
                                   ebs.get('volumeId'), ebs.get('attachTime'),
                                   ebs.get('deleteOnTermination')))
            # The EC2 tools have a couple more fields that I haven't been
            # able to identify.  If you figure out what they are, please send
            # a patch.
        elif self.args['Attribute'] == 'groupSet':
            # TODO:  test this in the wild (I don't have a VPC to work with)
            groups = (group.get('groupId') or group.get('groupName')
                      for group in result.get('groupSet', []))
            print self.tabify(('groupSet', result.get('instanceId'),
                               ', '.join(groups)))
        elif self.args['Attribute'] == 'productCodes':
            # TODO:  test this in the wild (I don't have anything I can test
            #        it with)
            codes = (code.get('productCode') for code in
                     result.get('productCodes', []))
            print self.tabify(('productCodes', result.get('instanceId'),
                               ', '.join(codes)))
        elif self.args['Attribute'] == 'userData':
            userdata = base64.b64decode(result.get('userData', {})
                                        .get('value', ''))
            if userdata:
                print self.tabify(('userData', result.get('instanceId')))
                print userdata
            else:
                print self.tabify(('userData', result.get('instanceId'), None))
        else:
            attr = result.get(self.args['Attribute'])
            if isinstance(attr, dict) and 'value' in attr:
                attr = attr['value']
            print self.tabify((self.args['Attribute'],
                               result.get('instanceId'), attr))
