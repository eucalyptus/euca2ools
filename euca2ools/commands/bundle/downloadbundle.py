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


import os.path
import sys

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.commands.bundle.mixins import BundleDownloadingMixin
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.getobject import GetObject


class DownloadBundle(WalrusRequest, FileTransferProgressBarMixin,
                     BundleDownloadingMixin):
    DESCRIPTION = ('Download a bundled image from the cloud\n\nYou must run '
                   'euca-unbundle-image on the bundle you download to obtain '
                   'the original image.')
    ARGS = [Arg('-d', '--directory', default=".",
                help='''the directory to download the bundle parts to, or "-"
                to write the bundled image to stdout''')]

    # noinspection PyExceptionInherit
    def configure(self):
        WalrusRequest.configure(self)
        if self.args['directory'] == '-':
            self.args['directory'] = sys.stdout
        elif isinstance(self.args['directory'], basestring):
            if not os.path.exists(self.args['directory']):
                raise ArgumentError(
                    "argument -d/--directory: '{0}' does not exist"
                    .format(self.args['directory']))
            if not os.path.isdir(self.args['directory']):
                raise ArgumentError(
                    "argument -d/--directory: '{0}' is not a directory"
                    .format(self.args['directory']))
        # Otherwise we assume it is a file object

    # noinspection PyExceptionInherit
    def main(self):
        manifest = self.fetch_manifest(self.service)
        parts = self.map_bundle_parts_to_s3paths(manifest)
        if isinstance(self.args['directory'], basestring):
            # We're downloading to a directory, so download the manifest (if
            # possible) and each of the parts to there.
            manifest_s3path = self.get_manifest_s3path()
            manifest_dest = os.path.join(self.args['directory'],
                                         os.path.basename(manifest_s3path))
            self.log.info('downloading manifest %s to %s',
                          manifest_s3path, manifest_dest)
            req = GetObject(
                config=self.config, service=self.service,
                source=manifest_s3path, dest=manifest_dest,
                show_progress=self.args.get('show_progress', False))
            req.main()
            for part, part_s3path in parts:
                part.filename = os.path.join(self.args['directory'],
                                             os.path.basename(part_s3path))
                self.log.info('downloading part %s to %s',
                              part_s3path, part.filename)
                req = GetObject(
                    config=self.config, service=self.service,
                    source=part_s3path, dest=part.filename,
                    show_progress=self.args.get('show_progress', False))
                response = req.main()
                self.__check_part_sha1(part, part_s3path, response)
        else:
            # We're downloading to a file object, so skip the manifest and
            # download all parts to that file object.
            manifest_dest = None
            for part, part_s3path in parts:
                self.log.info('downloading part %s', part_s3path)
                req = GetObject(
                    config=self.config, service=self.service,
                    source=part_s3path, dest=self.args['directory'],
                    show_progress=self.args.get('show_progress', False))
                response = req.main()
                self.__check_part_sha1(part, part_s3path, response)
        return manifest, manifest_dest

    def print_result(self, result):
        manifest, manifest_filename = result
        if manifest_filename:
            print 'Wrote manifest', manifest_filename
            print >> sys.stderr, 'Wrote manifest', manifest_filename  ## XXX

    def __check_part_sha1(self, part, part_s3path, response):
        if response[part_s3path]['sha1'] != part.hexdigest:
            self.log.error('rejecting download due to manifest SHA1 '
                           'mismatch (expected: %s, actual: %s)',
                           part.hexdigest, response[part_s3path]['sha1'])
            raise RuntimeError('downloaded file {0} appears to be corrupt '
                               '(expected SHA1: {0}, actual: {1}'
                               .format(part.hexdigest,
                                       response[part_s3path]['sha1']))
