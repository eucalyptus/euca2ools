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
import datetime
import os.path
import tempfile

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError, ServerError
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.commands.ec2 import EC2Request
from euca2ools.commands.ec2.describeconversiontasks import \
    DescribeConversionTasks
from euca2ools.commands.ec2.mixins import S3AccessMixin
from euca2ools.commands.ec2.structures import ImportManifest, ImportImagePart
from euca2ools.commands.s3.deleteobject import DeleteObject
from euca2ools.commands.s3.headobject import HeadObject
from euca2ools.commands.s3.getobject import GetObject
from euca2ools.commands.s3.putobject import PutObject
from euca2ools.exceptions import AWSError
import euca2ools.util


class ResumeImport(EC2Request, S3AccessMixin, FileTransferProgressBarMixin):
    DESCRIPTION = 'Perform the upload step of an import task'
    ARGS = [Arg('source', metavar='FILE',
                help='file containing the disk image to import (required)'),
            Arg('-t', '--task', required=True,
                help='the ID of the import task to resume (required)'),
            Arg('-x', '--expires', metavar='DAYS', type=int, default=30,
                help='''how long the import manifest should remain valid, in
                days (default: 30 days)'''),
            # This is documented, but not implemented in ec2-resume-import
            Arg('--part-size', metavar='MiB', type=int, default=10,
                help=argparse.SUPPRESS),
            # These are not implemented
            Arg('--user-threads', type=int, help=argparse.SUPPRESS),
            Arg('--dont-verify-format', action='store_true',
                help=argparse.SUPPRESS),
            # This does no validation, but it does prevent taking action
            Arg('--dry-run', action='store_true', help=argparse.SUPPRESS)]

    def configure(self):
        EC2Request.configure(self)
        self.configure_s3_access()
        if not self.args.get('expires'):
            self.args['expires'] = 30
        if self.args['expires'] < 1:
            raise ArgumentError(
                'argument -x/--expires: value must be positive')

    def main(self):
        if self.args.get('dry_run'):
            return

        if self.args.get('show_progress', False):
            print 'Uploading image for task', self.args['task']

        # Manifest
        desc_conv = DescribeConversionTasks.from_other(
            self, ConversionTaskId=[self.args['task']])
        task = desc_conv.main()['conversionTasks'][0]
        assert task['conversionTaskId'] == self.args['task']

        if task.get('importVolume'):
            vol_container = task['importVolume']
        else:
            vol_container = task['importInstance']['volumes'][0]
        file_size = euca2ools.util.get_filesize(self.args['source'])
        manifest = self.__get_or_create_manifest(vol_container, file_size)
        file_size_from_manifest = manifest.image_parts[len(
                                manifest.image_parts)-1].end + 1
        if file_size_from_manifest != file_size:
            raise ArgumentError(
                'file "{0}" is not the same size as the file the import '
                'started with (expected: {1}, actual: {2})'
                .format(self.args['source'],file_size_from_manifest,file_size))

        # Now we have a manifest; check to see what parts are already uploaded
        _, bucket, _ = self.args['s3_service'].resolve_url_to_location(
            vol_container['image']['importManifestUrl'])
        pbar_label_template = euca2ools.util.build_progressbar_label_template(
            [os.path.basename(part.key) for part in manifest.image_parts])
        for part in manifest.image_parts:
            part_s3path = '/'.join((bucket, part.key))
            head_req = HeadObject.from_other(
                self, service=self.args['s3_service'],
                auth=self.args['s3_auth'], path=part_s3path)
            try:
                head_req.main()
            except AWSError as err:
                if err.status_code == 404:
                    self.__upload_part(part, part_s3path, pbar_label_template)
                else:
                    raise
            # If it is already there we skip it

    def __get_or_create_manifest(self, vol_container, file_size):
        _, bucket, key = self.args['s3_service'].resolve_url_to_location(
            vol_container['image']['importManifestUrl'])
        manifest_s3path = '/'.join((bucket, key))
        try:
            with tempfile.SpooledTemporaryFile(max_size=1024000) as \
                    manifest_destfile:
                get_req = GetObject.from_other(
                    self, service=self.args['s3_service'],
                    auth=self.args['s3_auth'], source=manifest_s3path,
                    dest=manifest_destfile, show_progress=False)
                get_req.main()
                self.log.info('using existing import manifest from the server')
                manifest_destfile.seek(0)
                manifest = ImportManifest.read_from_fileobj(
                    manifest_destfile)
        except ServerError as err:
            if err.status_code == 404:
                self.log.info('creating new import manifest')
                manifest = self.__generate_manifest(vol_container, file_size)
                tempdir = tempfile.mkdtemp()
                manifest_filename = os.path.join(tempdir,
                                                 os.path.basename(key))
                with open(manifest_filename, 'w') as manifest_file:
                    manifest.dump_to_fileobj(manifest_file, pretty_print=True)
                put_req = PutObject.from_other(
                    get_req, source=manifest_filename, dest=manifest_s3path,
                    show_progress=False)
                put_req.main()
                os.remove(manifest_filename)
                os.rmdir(tempdir)
            else:
                raise
        return manifest

    def __generate_manifest(self, vol_container, file_size):
        days = self.args.get('expires') or 30
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days)
        _, bucket, key = self.args['s3_service'].resolve_url_to_location(
            vol_container['image']['importManifestUrl'])
        key_prefix = key.rsplit('/', 1)[0]
        manifest = ImportManifest(loglevel=self.log.level)
        manifest.file_format = vol_container['image']['format']
        delete_req = DeleteObject.from_other(
            self, service=self.args['s3_service'], auth=self.args['s3_auth'],
            path='/'.join((bucket, key)))
        manifest.self_destruct_url = delete_req.get_presigned_url(expiration)
        manifest.image_size = int(vol_container['image']['size'])
        manifest.volume_size = int(vol_container['volume']['size'])
        part_size = (self.args.get('part_size') or 10) * 2 ** 20  # MiB
        for index, part_start in enumerate(xrange(0, file_size, part_size)):
            part = ImportImagePart()
            part.index = index
            part.start = part_start
            part.end = min(part_start + part_size, file_size) - 1
            part.key = '{0}/{1}.part.{2}'.format(
                key_prefix, os.path.basename(self.args['source']), index)
            part_path = '/'.join((bucket, part.key))
            head_req = HeadObject.from_other(delete_req, path=part_path)
            get_req = GetObject.from_other(delete_req, source=part_path)
            delete_req = DeleteObject.from_other(delete_req, path=part_path)
            part.head_url = head_req.get_presigned_url(expiration)
            part.get_url = get_req.get_presigned_url(expiration)
            part.delete_url = delete_req.get_presigned_url(expiration)
            manifest.image_parts.append(part)
        return manifest

    def __upload_part(self, part, part_s3path, pbar_label_template):
        self.log.info('Uploading part %s (bytes %i-%i)', part_s3path,
                      part.start, part.end)
        part_pbar_label = pbar_label_template.format(
            fname=os.path.basename(part.key), index=(part.index + 1))
        with open(self.args['source']) as source:
            source.seek(part.start)
            put_req = PutObject.from_other(
                self, service=self.args['s3_service'],
                auth=self.args['s3_auth'], source=source, dest=part_s3path,
                size=(part.end - part.start + 1),
                show_progress=self.args.get('show_progress', False),
                progressbar_label=part_pbar_label)
            return put_req.main()
