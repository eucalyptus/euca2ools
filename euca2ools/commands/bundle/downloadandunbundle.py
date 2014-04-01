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
import sys

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.bundle.util import open_pipe_fileobjs
from euca2ools.bundle.util import waitpid_in_thread
from euca2ools.commands.bundle.downloadbundle import DownloadBundle
from euca2ools.commands.bundle.mixins import BundleDownloadingMixin
from euca2ools.commands.bundle.unbundlestream import UnbundleStream
from euca2ools.commands.s3 import WalrusRequest


class DownloadAndUnbundle(WalrusRequest, FileTransferProgressBarMixin,
                          BundleDownloadingMixin):
    DESCRIPTION = ('Download and unbundle a bundled image from the cloud\n\n '
                   'The key used to unbundle the image must match a '
                   'certificate that was used to bundle it.')
    ARGS = [Arg('-d', '--destination', dest='dest', metavar='(FILE | DIR)',
                default=".", help='''where to place the unbundled image
                (default: current directory)'''),
            Arg('-k', '--privatekey',
                help='''file containing the private key to decrypt the bundle
                with.  This must match a certificate used when bundling the
                image.''')]

    # noinspection PyExceptionInherit
    def configure(self):
        WalrusRequest.configure(self)

        # The private key could be the user's or the cloud's.  In the config
        # this is a user-level option.
        if not self.args.get('privatekey'):
            config_privatekey = self.config.get_user_option('private-key')
            if self.args.get('userregion'):
                self.args['privatekey'] = config_privatekey
            elif 'EC2_PRIVATE_KEY' in os.environ:
                self.args['privatekey'] = os.getenv('EC2_PRIVATE_KEY')
            elif config_privatekey:
                self.args['privatekey'] = config_privatekey
            else:
                raise ArgumentError(
                    'missing private key; please supply one with -k')
        self.args['privatekey'] = os.path.expanduser(os.path.expandvars(
            self.args['privatekey']))
        if not os.path.exists(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' does not exist"
                                .format(self.args['privatekey']))
        if not os.path.isfile(self.args['privatekey']):
            raise ArgumentError("private key file '{0}' is not a file"
                                .format(self.args['privatekey']))
        self.log.debug('private key: %s', self.args['privatekey'])

    def __open_dest(self, manifest):
        if self.args['dest'] == '-':
            self.args['dest'] = sys.stdout
            self.args['show_progress'] = False
        elif isinstance(self.args['dest'], basestring):
            if os.path.isdir(self.args['dest']):
                image_filename = os.path.join(self.args['dest'],
                                              manifest.image_name)
            else:
                image_filename = self.args['dest']
            self.args['dest'] = open(image_filename, 'w')
            return image_filename
        # Otherwise we assume it's a file object

    def main(self):
        manifest = self.fetch_manifest(
            self.service, privkey_filename=self.args['privatekey'])
        download_out_r, download_out_w = open_pipe_fileobjs()
        try:
            self.__create_download_pipeline(download_out_w)
        finally:
            download_out_w.close()
        image_filename = self.__open_dest(manifest)
        unbundlestream = UnbundleStream(
            config=self.config, source=download_out_r, dest=self.args['dest'],
            enc_key=manifest.enc_key, enc_iv=manifest.enc_iv,
            image_size=manifest.image_size, sha1_digest=manifest.image_digest,
            show_progress=self.args.get('show_progress', False))
        unbundlestream.main()
        return image_filename

    def __create_download_pipeline(self, outfile):
        downloadbundle = DownloadBundle(
            service=self.service, config=self.config, dest=outfile,
            bucket=self.args['bucket'], manifest=self.args.get('manifest'),
            local_manifest=self.args.get('local_manifest'),
            show_progress=False)
        downloadbundle_p = multiprocessing.Process(target=downloadbundle.main)
        downloadbundle_p.start()
        waitpid_in_thread(downloadbundle_p.pid)
        outfile.close()

    def print_result(self, image_filename):
        if (image_filename and
                self.args['dest'].fileno() != sys.stdout.fileno()):
            print 'Wrote', image_filename
