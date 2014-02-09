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

import os
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
from euca2ools.bundle.manifest import BundleManifest
from euca2ools.bundle.util import open_pipe_fileobjs, spawn_process
from euca2ools.bundle.util import waitpid_in_thread
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.bundle.downloadbundle import DownloadBundle
from euca2ools.commands.bundle2.unbundlestream import UnbundleStream


class DownloadUnbundle(WalrusRequest, FileTransferProgressBarMixin):
    DESCRIPTION = ('Download and unbundle a bundled image from the cloud\n')
    ARGS = [Arg('-b', '--bucket', required=True,
                help='''Bucket to download the bucket from (required)'''),
            MutuallyExclusiveArgList(
                Arg('-m', '--manifest', dest='manifest',
                    help='''Use a local manifest file to figure out what to
                    download'''),
                Arg('-p', '--prefix',
                    help='''Download the bundle that begins with a specific
                    prefix (e.g. "fry" for "fry.manifest.xml")''')),
            Arg('-d', '--directory', default=".",
                help='''The directory to download the bundle image to.'''),
            Arg('--maxbytes', default=0,
                help='''The Maximum bytes allowed to be written when
                using 'destination'.'''),
            Arg('-k', '--privatekey',
                help='''File containing the private key to decrypt the bundle
                with.  This must match the certificate used when bundling the
                image.''')]

    # noinspection PyExceptionInherit
    def configure(self):
        #Get the mandatory private key...
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

        #Get optional destination directory...
        dest_dir = self.args['directory']
        if not (dest_dir == "-"):
            dest_dir = os.path.expanduser(os.path.abspath(dest_dir))
            if not os.path.exists(dest_dir):
                raise ArgumentError("Destination directory '{0}' "
                                    "does not exist"
                                    .format(dest_dir))
            if not os.path.isdir(dest_dir):
                raise ArgumentError("Destination '{0}' is not Directory"
                                    .format(dest_dir))
        else:
            self.args['show_progress'] = False
        self.args['directory'] = dest_dir

        #Get the manifest...
        if self.args.get('manifest'):
            if not isinstance(self.args.get('manifest'), BundleManifest):
                manifest = os.path.expanduser(os.path.abspath(
                    self.args['manifest']))
                if not os.path.exists(manifest):
                    raise ArgumentError("Manifest '{0}' does not exist"
                                        .format(self.args['manifest']))
                if not os.path.isfile(manifest):
                    raise ArgumentError("Manifest '{0}' is not a file"
                                        .format(self.args['manifest']))
                #Read manifest into BundleManifest obj...
                self.args['manifest'] = (BundleManifest.
                                         read_from_file(manifest,
                                                        self.args['privatekey']
                                                        ))

    def _downloadbundle_wrapper(self, downloadbundle_obj, outfile):
        try:
            downloadbundle_obj.main()
        except KeyboardInterrupt:
            print 'Caught keyboard interrupt'
            return
        finally:
            if outfile:
                outfile.close()

    def main(self):
        dest_dir = self.args.get('directory')
        bucket = self.args.get('bucket').split('/', 1)[0]
        manifest = self.args.get('manifest', None)
        self.log.debug('bucket:{0} directory:{1}'.format(bucket, dest_dir))
        #Created download bundle obj...
        downloadbundle_r, downloadbundle_w = open_pipe_fileobjs()
        kwargs = {'directory': downloadbundle_w,
                  'show_progress': False,
                  'manifest': self.args.get('manifest', None),
                  'bucket': self.args.get('bucket'),
                  'prefix': self.args.get('prefix'),
                  'service': self.service,
                  'config': self.config}
        downloadbundle = DownloadBundle(**kwargs)
        downloadbundle.args['directory'] = downloadbundle_w
        #If a local manifest wasn't provided attempt to read in a remote
        if not manifest:
            manifest = downloadbundle._get_manifest_obj()
        pbar = None
        if self.args.get('show_progress'):
            try:
                if self.args.get('show_progress'):
                    label = self.args.get('progressbar_label',
                                          'Download -> UnBundling')
                    pbar = self.get_progressbar(label=label,
                                                maxval=manifest.image_size)
            except NameError:
                pass

        #Setup the destination fileobj...
        if dest_dir == "-":
            #Write to stdout
            dest_file = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
            dest_file_name = None
        else:
            #write to local file path...
            dest_file = open(dest_dir + "/" + manifest.image_name, 'w')
            dest_file_name = dest_file.name
            #check for avail space if the resulting image size is known
            if manifest:
                d_stat = os.statvfs(dest_file_name)
                avail_space = d_stat.f_frsize * d_stat.f_favail
                if manifest.image_size > avail_space:
                    raise ValueError('Image size:{0} exceeds destination free '
                                     'space:{1}'
                                     .format(manifest.image_size, avail_space))

        download = spawn_process(self._downloadbundle_wrapper,
                                 downloadbundle_obj=downloadbundle,
                                 outfile=downloadbundle_w)
        downloadbundle_w.close()
        waitpid_in_thread(download.pid)

        digest = UnbundleStream(source=downloadbundle_r,
                                destination=dest_file,
                                enc_key=manifest.enc_key,
                                enc_iv=manifest.enc_iv,
                                progressbar=pbar,
                                maxbytes=self.args.get('maxbytes'),
                                config=self.config).main()

        digest = digest.strip()
        #Verify the Checksum from the unbundle operation matches manifest
        if digest != manifest.image_digest:
            raise ValueError('Extracted image appears to be corrupt '
                             '(expected digest: {0}, actual: {1})'
                             .format(manifest.image_digest, digest))
        self.log.debug("\nExpected digest:{0}\n  Actual digest:{1}"
                       .format(str(manifest.image_digest), str(digest)))
        return dest_file_name

    def print_result(self, result):
        if result:
            print "Bundle downloaded to '{0}'".format(result)

if __name__ == '__main__':
    DownloadUnbundle.run()
