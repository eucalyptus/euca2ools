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

import tempfile

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.ec2 import EC2Request
from euca2ools.commands.ec2.describeconversiontasks import \
    DescribeConversionTasks
from euca2ools.commands.ec2.mixins import S3AccessMixin
from euca2ools.commands.ec2.structures import ImportManifest
from euca2ools.commands.s3.deleteobject import DeleteObject
from euca2ools.commands.s3.getobject import GetObject
from euca2ools.exceptions import AWSError


class DeleteDiskImage(EC2Request, S3AccessMixin):
    DESCRIPTION = 'Delete a disk image used for an import task'
    ARGS = [MutuallyExclusiveArgList(
                Arg('-t', '--task',
                    help='ID of the task to delete the image from'),
                Arg('-u', '--manifest-url',
                    help='location of the import manifest'))
            .required(),
            Arg('--ignore-active-task', action='store_true',
                help='''delete the image even if the import task is active
                (only works with -t/--task)''')]

    def configure(self):
        EC2Request.configure(self)
        self.configure_s3_access()
        if self.args.get('ignore_active_task') and not self.args.get('task'):
            raise ArgumentError('argument --ignore-active-task my only be '
                                'used with -t/--task')

    def main(self):
        if self.args.get('manifest_url'):
            manifest_url = self.args['manifest_url']
        if self.args.get('task'):
            desc_conv = DescribeConversionTasks.from_other(
                self, ConversionTaskId=[self.args['task']])
            task = desc_conv.main()['conversionTasks'][0]
            assert task['conversionTaskId'] == self.args['task']
            if task.get('importVolume'):
                vol_container = task['importVolume']
            else:
                vol_container = task['importInstance']['volumes'][0]
            manifest_url = vol_container['image']['importManifestUrl']
        _, bucket, key = self.args['s3_service'].resolve_url_to_location(
            manifest_url)
        manifest_s3path = '/'.join((bucket, key))
        manifest = self.__download_manifest(manifest_s3path)

        for part in manifest.image_parts:
            delete_req = DeleteObject.from_other(
                self, service=self.args['s3_service'],
                auth=self.args['s3_auth'], path='/'.join((bucket, part.key)))
            delete_req.main()
        delete_req = DeleteObject.from_other(
            self, service=self.args['s3_service'], auth=self.args['s3_auth'],
            path=manifest_s3path)
        delete_req.main()

    def __download_manifest(self, s3path):
        with tempfile.SpooledTemporaryFile(max_size=1024000) as \
                manifest_destfile:
            get_req = GetObject.from_other(
                self, service=self.args['s3_service'],
                auth=self.args['s3_auth'], source=s3path,
                dest=manifest_destfile, show_progress=False)
            try:
                get_req.main()
            except AWSError as err:
                if err.status_code == 404:
                    raise ArgumentError('import manifest "{0}" does not exist'
                                        .format(s3path))
                raise
            manifest_destfile.seek(0)
            return ImportManifest.read_from_fileobj(manifest_destfile)
