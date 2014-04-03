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
from requestbuilder import Arg, Filter, GenericTagFilter


class DescribeVolumes(EC2Request):
    DESCRIPTION = 'Display information about volumes'
    ARGS = [Arg('VolumeId', metavar='VOLUME', nargs='*',
                help='limit results to specific volumes')]
    FILTERS = [Filter('attachment.attach-time', help='attachment start time'),
               Filter('attachment.delete-on-termination', help='''whether the
                      volume will be deleted upon instance termination'''),
               Filter('attachment.device',
                      help='device node exposed to the instance'),
               Filter('attachment.instance-id',
                      help='ID of the instance the volume is attached to'),
               Filter('attachment.status', help='attachment state'),
               Filter('availability-zone'),
               Filter('create-time', help='creation time'),
               Filter('size', type=int, help='size in GiB'),
               Filter('snapshot-id',
                      help='snapshot from which the volume was created'),
               Filter('status'),
               Filter('tag-key', help='key of a tag assigned to the volume'),
               Filter('tag-value',
                      help='value of a tag assigned to the volume'),
               GenericTagFilter('tag:KEY',
                                help='specific tag key/value combination'),
               Filter(name='volume-id'),
               Filter(name='volume-type')]
    LIST_TAGS = ['volumeSet', 'attachmentSet', 'tagSet']

    def print_result(self, result):
        for volume in result.get('volumeSet'):
            self.print_volume(volume)
