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
from euca2ools.commands.s3 import S3Request


class DownloadBundle(S3Request, FileTransferProgressBarMixin,
                     BundleDownloadingMixin):
    DESCRIPTION = ('Download a bundled image from the cloud\n\nYou must run '
                   'euca-unbundle-image on the bundle you download to obtain '
                   'the original image.')
    ARGS = [Arg('-d', '--directory', dest='dest', metavar='DIR', default=".",
                help='''the directory to download the bundle parts to, or "-"
                to write the bundled image to stdout''')]

    # noinspection PyExceptionInherit
    def configure(self):
        S3Request.configure(self)
        if self.args['dest'] == '-':
            self.args['dest'] = sys.stdout
            self.args['show_progress'] = False
        elif isinstance(self.args['dest'], basestring):
            if not os.path.exists(self.args['dest']):
                raise ArgumentError(
                    "argument -d/--directory: '{0}' does not exist"
                    .format(self.args['dest']))
            if not os.path.isdir(self.args['dest']):
                raise ArgumentError(
                    "argument -d/--directory: '{0}' is not a directory"
                    .format(self.args['dest']))
        # Otherwise we assume it is a file object

    # noinspection PyExceptionInherit
    def main(self):
        manifest = self.fetch_manifest(self.service)
        if isinstance(self.args['dest'], basestring):
            manifest_dest = self.download_bundle_to_dir(
                manifest, self.args['dest'], self.service)
        else:
            manifest_dest = self.download_bundle_to_fileobj(
                manifest, self.args['dest'], self.service)
        return manifest, manifest_dest

    def print_result(self, result):
        _, manifest_filename = result
        if (manifest_filename and
            (isinstance(self.args['dest'], basestring) or
             self.args['dest'].fileno() != sys.stdout.fileno())):
            print 'Wrote manifest', manifest_filename
