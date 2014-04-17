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

import argparse

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.argtypes import b64encoded_file_contents
from euca2ools.commands.ec2 import EC2Request


def _min_ec2_block_device_mapping(map_as_str):
    try:
        device, mapping = map_as_str.split('=')
    except ValueError:
        raise argparse.ArgumentTypeError(
            'block device mapping "{0}" must have form DEVICE=::true or '
            'DEVICE=::false'.format(map_as_str))
    mapping_bits = mapping.split(':')
    if (len(mapping_bits) != 3 or mapping_bits[0] or mapping_bits[1] or
            mapping_bits[2] not in ('true', 'false')):
        raise argparse.ArgumentTypeError(
            'block device mapping "{0}" must be either {1}=::true or '
            '{1}=::false'.format(map_as_str, device))
    return {'DeviceName': device,
            'Ebs': {'DeleteOnTermination': mapping_bits[2]}}


class ModifyInstanceAttribute(EC2Request):
    DESCRIPTION = 'Modify an attribute of an instance'
    ARGS = [Arg('InstanceId', metavar='INSTANCE',
                help='ID of the instance to modify (required)'),
            MutuallyExclusiveArgList(
                Arg('-b', '--block-device-mapping', dest='BlockDeviceMapping',
                    action='append', metavar='DEVICE=::(true|false)',
                    type=_min_ec2_block_device_mapping, default=[],
                    help='''change whether a volume attached to the instance
                    will be deleted upon the instance's termination'''),
                Arg('--disable-api-termination', choices=('true', 'false'),
                    dest='DisableApiTermination.Value', help='''change whether
                    or not the instance may be terminated'''),
                Arg('--ebs-optimized', dest='EbsOptimized',
                    choices=('true', 'false'), help='''change whether or not
                    the instance should be optimized for EBS I/O'''),
                Arg('-g', '--group-id', dest='GroupId', metavar='GROUP',
                    action='append', default=[], help='''[VPC only] Change the
                    security group(s) the instance is in'''),
                Arg('--instance-initiated-shutdown-behavior',
                    dest='InstanceInitiatedShutdownBehavior.Value',
                    choices=('stop', 'terminate'), help='''whether to stop or
                    terminate the EBS instance when it shuts down
                    (instance-store instances are always terminated)'''),
                Arg('-t', '--instance-type', metavar='INSTANCETYPE',
                    help="change the instance's type"),
                Arg('--kernel', dest='Kernel.Value', metavar='IMAGE',
                    help="change the instance's kernel image"),
                Arg('--ramdisk', dest='Ramdisk.Value', metavar='IMAGE',
                    help="change the instance's ramdisk image"),
                Arg('--source-dest-check', dest='SourceDestCheck.Value',
                    choices=('true', 'false'), help='''change whether
                    source/destination address checking is enabled'''),
                Arg('--sriov', dest='SriovNetSupport.Value', metavar='simple',
                    choices=('simple',), help='''enable enhanced networking for
                    the instance and its descendants'''),
                Arg('--user-data', dest='UserData.Value', metavar='DATA',
                    help='''change the instance's user data (must be
                    base64-encoded)'''),
                Arg('--user-data-file', dest='UserData.Value', metavar='FILE',
                    type=b64encoded_file_contents, help='''change the
                    instance's user data to the contents of a file'''))
            .required()]
