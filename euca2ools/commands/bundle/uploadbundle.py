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

import multiprocessing
import os.path

from requestbuilder import Arg
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.bundle.manifest import BundleManifest
from euca2ools.commands.bundle.mixins import BundleUploadingMixin
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.putobject import PutObject


class UploadBundle(WalrusRequest, BundleUploadingMixin,
                   FileTransferProgressBarMixin):
    DESCRIPTION = 'Upload a bundle prepared by euca-bundle-image to the cloud'
    ARGS = [Arg('-m', '--manifest', metavar='FILE', required=True,
                help='manifest for the bundle to upload (required)'),
            Arg('-d', '--directory', metavar='DIR',
                help='''directory that contains the bundle parts (default:
                directory that contains the manifest)'''),
            ## TODO:  make this work
            Arg('--part', metavar='INT', type=int, default=0, help='''begin
                uploading with a specific part number (default: 0)'''),
            Arg('--skipmanifest', action='store_true',
                help='do not upload the manifest')]

    def main(self):
        key_prefix = self.get_bundle_key_prefix()
        self.ensure_dest_bucket_exists()

        manifest = BundleManifest.read_from_file(self.args['manifest'])
        part_dir = (self.args.get('directory') or
                    os.path.dirname(self.args['manifest']))
        for part in manifest.image_parts:
            part.filename = os.path.join(part_dir, part.filename)
            if not os.path.isfile(part.filename):
                raise ValueError("no such part: '{0}'".format(part.filename))

        # manifest -> upload
        part_out_r, part_out_w = multiprocessing.Pipe(duplex=False)
        part_gen = multiprocessing.Process(target=_generate_bundle_parts,
                                           args=(manifest, part_out_w))
        part_gen.start()
        part_out_w.close()

        # Drive the upload process by feeding in part info
        self.upload_bundle_parts(part_out_r, key_prefix,
                                 show_progress=self.args.get('show_progress'))
        part_gen.join()

        # (conditionally) upload the manifest
        if not self.args.get('skip_manifest'):
            manifest_dest = (key_prefix +
                             os.path.basename(self.args['manifest']))
            req = PutObject(source=self.args['manifest'], dest=manifest_dest,
                            acl=self.args.get('acl') or 'aws-exec-read',
                            retries=self.args.get('retries') or 0,
                            service=self.service, config=self.config)
            req.main()
        else:
            manifest_dest = None

        return {'parts': tuple({'filename': part.filename,
                                'key': (key_prefix +
                                        os.path.basename(part.filename))}
                               for part in manifest.image_parts),
                'manifests': ({'filename': self.args['manifest'],
                               'key': manifest_dest},)}

    def print_result(self, result):
        if self.debug:
            for part in result['parts']:
                print 'Uploaded', part['key']
        if result['manifests'][0]['key'] is not None:
            print 'Uploaded', result['manifests'][0]['key']


def _generate_bundle_parts(manifest, out_mpconn):
    try:
        for part in manifest.image_parts:
            assert os.path.isfile(part.filename)
            out_mpconn.send(part)
    finally:
        out_mpconn.close()
