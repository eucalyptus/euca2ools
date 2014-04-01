# Copyright 2009-2013 Eucalyptus Systems, Inc.
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
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError


class CreateVolume(EC2Request):
    DESCRIPTION = 'Create a new volume'
    ARGS = [Arg('-z', '--availability-zone', dest='AvailabilityZone',
                metavar='ZONE', required=True, help='''availability zone in
                which to create the new volume (required)'''),
            Arg('-s', '--size', dest='Size', type=int, help='''size of the new
                volume in GiB (required unless --snapshot is used)'''),
            Arg('--snapshot', dest='SnapshotId', metavar='SNAPSHOT',
                help='snapshot from which to create the new volume'),
            Arg('-t', '--type', dest='VolumeType', metavar='VOLTYPE',
                help='volume type'),
            Arg('-i', '--iops', dest='Iops', type=int,
                help='number of I/O operations per second')]

    # noinspection PyExceptionInherit
    def configure(self):
        EC2Request.configure(self)
        if not self.args.get('Size') and not self.args.get('SnapshotId'):
            raise ArgumentError('-s/--size or --snapshot must be specified')
        if self.args.get('Iops') and not self.args.get('VolumeType'):
            raise ArgumentError('argument -i/--iops: -t/--type is required')
        if self.args.get('Iops') and self.args.get('VolumeType') == 'standard':
            raise ArgumentError(
                'argument -i/--iops: not allowed with volume type "standard"')

    def print_result(self, result):
        print self.tabify(('VOLUME', result.get('volumeId'),
                           result.get('size'), result.get('snapshotId'),
                           result.get('availabilityZone'),
                           result.get('status'), result.get('createTime')))
