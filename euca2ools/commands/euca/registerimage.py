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

from euca2ools.commands.argtypes import ec2_block_device_mapping
from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError


class RegisterImage(EucalyptusRequest):
    DESCRIPTION = 'Register a new image'
    ARGS = [Arg('ImageLocation', metavar='MANIFEST', nargs='?',
                help='''location of the image manifest in S3 storage
                (required for instance-store images)'''),
            Arg('-n', '--name', dest='Name', required=True,
                help='name of the new image (required)'),
            Arg('-d', '--description', dest='Description',
                help='description of the new image'),
            Arg('-a', '--architecture', dest='Architecture',
                choices=('i386', 'x86_64', 'armhf'),
                help='CPU architecture of the new image'),
            Arg('--kernel', dest='KernelId', metavar='KERNEL',
                help='ID of the kernel to associate with the new image'),
            Arg('--ramdisk', dest='RamdiskId', metavar='RAMDISK',
                help='ID of the ramdisk to associate with the new image'),
            Arg('--root-device-name', dest='RootDeviceName', metavar='DEVICE',
                help='root device name (default: /dev/sda1)'),
            # ^ default is added by main()
            Arg('-s', '--snapshot', route_to=None,
                help='snapshot to use for the root device'),
            Arg('-b', '--block-device-mapping', metavar='DEVICE=MAPPED',
                dest='BlockDeviceMapping', action='append',
                type=ec2_block_device_mapping, default=[],
                help='''define a block device mapping for the image, in the
                form DEVICE=MAPPED, where "MAPPED" is "none", "ephemeral(0-3)",
                or
                "[SNAP-ID]:[SIZE]:[true|false]:[standard|VOLTYPE[:IOPS]]"'''),
            Arg('--virtualization-type', dest='VirtualizationType',
                choices=('paravirtual', 'hvm'),
                help='[Privileged] virtualization type for the new image'),
            Arg('--platform', dest='Platform', metavar='windows',
                choices=('windows',),
                help="[Privileged] the new image's platform (windows)")]

    # noinspection PyExceptionInherit
    def preprocess(self):
        if self.args.get('ImageLocation'):
            # instance-store image
            if self.args.get('RootDeviceName'):
                raise ArgumentError('argument --root-device-name: not allowed '
                                    'with argument MANIFEST')
            if self.args.get('snapshot'):
                raise ArgumentError('argument --snapshot: not allowed with '
                                    'argument MANIFEST')
        else:
            # Try for an EBS image
            if not self.params.get('RootDeviceName'):
                self.params['RootDeviceName'] = '/dev/sda1'
            snapshot = self.args.get('snapshot')
            # Look for a mapping for the root device
            for mapping in self.args['BlockDeviceMapping']:
                if mapping.get('DeviceName') == self.args['RootDeviceName']:
                    if (snapshot != mapping.get('Ebs', {}).get('SnapshotId')
                            and snapshot):
                        # The mapping's snapshot differs or doesn't exist
                        raise ArgumentError(
                            'snapshot ID supplied with --snapshot conflicts '
                            'with block device mapping for root device {0}'
                            .format(mapping['DeviceName']))
                    else:
                        # No need to apply --snapshot since the mapping is
                        # already there
                        break
            else:
                if snapshot:
                    self.params['BlockDeviceMapping'].append(
                        {'DeviceName': self.args['RootDeviceName'],
                         'Ebs': {'SnapshotId': snapshot}})
                else:
                    raise ArgumentError(
                        'either a manifest location or a root device snapshot '
                        'mapping must be specified')

    def print_result(self, result):
        print self.tabify(('IMAGE', result.get('imageId')))
