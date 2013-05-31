# Copyright 2013 Eucalyptus Systems, Inc.
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
from euca2ools.commands.argtypes import (delimited_list,
    ec2_block_device_mapping)
from euca2ools.commands.autoscaling import AutoScalingRequest
import os.path
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError


class CreateLaunchConfiguration(AutoScalingRequest):
    DESCRIPTION = 'Create a new auto-scaling instance launch configuration'
    ARGS = [Arg('LaunchConfigurationName', metavar='LAUNCHCONFIG',
                help='name of the new launch configuration (required)'),
            Arg('-i', '--image-id', dest='ImageId', metavar='IMAGE',
                required=True,
                help='machine image to use for instances (required)'),
            Arg('-t', '--instance-type', dest='InstanceType', metavar='TYPE',
                required=True,
                help='instance type for use for instances (required)'),
            Arg('--block-device-mapping', dest='BlockDeviceMappings.member',
                metavar='DEVICE1=MAPPED1,DEVICE2=MAPPED2,...',
                type=delimited_list(','), help='''a comma-separated list of
                block device mappings for the image, in the form DEVICE=MAPPED,
                where "MAPPED" is "none", "ephemeral(0-3)", or
                "[SNAP-ID]:[SIZE]:[true|false]'''),
            Arg('--ebs-optimized', dest='EbsOptimized', action='store_const',
                const='true',
                help='whether the instance is optimized for EBS I/O'),
            Arg('--group', dest='SecurityGroups.member',
                metavar='GROUP1,GROUP2,...', type=delimited_list(','),
                help='''a comma-separated list of security groups with which
                to associate instances.  Either all group names or all group
                IDs are allowed, but not both.'''),
            Arg('--iam-instance-profile', dest='IamInstanceProfile',
                metavar='PROFILE', help='''ARN of the instance profile
                associated with instances' IAM roles'''),
            Arg('--kernel', dest='KernelId', metavar='KERNEL',
                help='kernel image to use for instances'),
            Arg('--key', dest='KeyName', metavar='KEYPAIR',
                help='name of the key pair to use for instances'),
            Arg('--monitoring-enabled', dest='InstanceMonitoring.Enabled',
                action='store_const', const='true',
                help='enable detailed monitoring (enabled by default)'),
            Arg('--monitoring-disabled', dest='InstanceMonitoring.Enabled',
                action='store_const', const='false',
                help='disable detailed monitoring (enabled by default)'),
            Arg('--ramdisk', dest='RamdiskId', metavar='RAMDISK',
                help='ramdisk image to use for instances'),
            Arg('--spot-price', dest='SpotPrice', metavar='PRICE',
                help='maximum hourly price for any spot instances launched'),
            MutuallyExclusiveArgList(
                Arg('-d', '--user-data', metavar='DATA', route_to=None,
                    help='user data to make available to instances'),
                Arg('--user-data-force', metavar='DATA', route_to=None,
                    help='''same as -d/--user-data, but without checking if a
                    file by that name exists first'''),
                Arg('-f', '--user-data-file', metavar='FILE', route_to=None,
                    help='''file containing user data to make available to
                    instances'''))]

    def configure(self):
        AutoScalingRequest.configure(self)
        if self.args.get('user_data'):
            if os.path.isfile(self.args['user_data']):
                raise ArgumentError(
                    'argument -d/--user-data: to pass the contents of a file '
                    'as user data, use -f/--user-data-file.  To pass the '
                    "literal value '{0}' as user data even though it matches "
                    'the name of a file, use --user-data-force.')
            else:
                self.params['UserData'] = base64.b64encode(
                    self.args['user_data'])
        elif self.args.get('user_data_force'):
            self.params['UserData'] = base64.b64encode(
                self.args['user_data_force'])
        elif self.args.get('user_data_file'):
            with open(self.args['user_data_file']) as user_data_file:
                self.params['UserData'] = base64.b64encode(
                    user_data_file.read())

    def preprocess(self):
        if self.args.get('block_device_mapping'):
            mappings = map(ec2_block_device_mapping,
                           self.args['block_device_mapping'])
            self.params['BlockDeviceMappings.member'] = mappings
