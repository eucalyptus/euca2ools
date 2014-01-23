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

from euca2ools.commands import Euca2ools
from euca2ools.commands.walrus.getobject import GetObject
from euca2ools.bundle.manifest import BundleManifest
from euca2ools.bundle.util import open_pipe_fileobjs, spawn_process
from euca2ools.bundle.util import close_all_fds, waitpid_in_thread
from euca2ools.bundle.pipes.core import create_unbundle_pipeline
import euca2ools.bundle.pipes
from euca2ools.commands.bundle.helpers import download_files, get_manifest_keys
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.checkbucket import CheckBucket
from euca2ools.exceptions import AWSError
import os
import hashlib
from StringIO import  StringIO
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin


class DownloadBundle(WalrusRequest, FileTransferProgressBarMixin):
    DESCRIPTION = ('Download a bundled image from the cloud\n\nYou must run '
                   'euca-unbundle-image on the bundle you download to obtain '
                   'the original image.')
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
                help='''The directory to download the parts to.'''),
            Arg('-u', '--unbundle', default=False, action='store_true',
                help='''Unbundle downloaded parts to an image'''),
            Arg('--maxbytes', default=0,
                help='''The Maximum bytes allowed to be written when
                using 'destination'.'''),
            Arg('-k', '--privatekey', required=True,
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
                raise ArgumentError("Destination directory '{0}' does not exist"
                .format(dest_dir))
            if not os.path.isdir(dest_dir):
                raise ArgumentError("Destination '{0}' is not Directory"
                .format(dest_dir))
        self.args['destination'] = dest_dir

        #Get themanifest...
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
                                                        self.args['privatekey']))

    def _get_manifest_obj(self):
        if self.args.get('manifest'):
            if isinstance(self.args.get('manifest'), BundleManifest):
                return self.args.get('manifest')
            else:
                #Read in manifest from local file path...
                manifest = os.path.expanduser(os.path.abspath(
                    self.args['manifest']))
                if not os.path.exists(manifest):
                    raise ArgumentError("Manifest '{0}' does not exist"
                    .format(manifest))
                if not os.path.isfile(manifest):
                    raise ArgumentError("Manifest '{0}' is not a file"
                    .format(manifest))
                    #Read manifest into BundleManifest obj...
                manifest = BundleManifest.read_from_file(manifest,
                                                         self.args['privatekey'])
        else:
            #Read in remote manifest via multi-process...
            bucket = self.args.get('bucket')
            prefix = self.args.get('prefix')
            #Make sure the manifest exists, and the prefix is unique...
            manifest_keys = get_manifest_keys(bucket, prefix, service=self.service,
                                              config=self.config)
            if not manifest_keys:
                if prefix:
                    raise ArgumentError(
                        "no manifests found with prefix '{0}' in bucket '{1}'."
                        .format(prefix, bucket))
                else:
                    raise ArgumentError("no manifests found in bucket '{0}'."
                    .format(bucket))
            if len(manifest_keys) > 1:
                raise RuntimeError('Multiple manifests found:{0}'
                .format(",".join(str(m) for m in manifest_keys)))
            #Read the manifest into an obj...
            manifest_r, manifest_w = open_pipe_fileobjs()
            manifest_key = manifest_keys.pop()
            try:
                download_manifest = spawn_process(self._download_file_to_fileobj,
                                                  bucket=bucket,
                                                  key=manifest_key,
                                                  fileobj=manifest_w)
                waitpid_in_thread(download_manifest.pid)
                manifest_w.close()
            except AWSError as err:
                if err.code != 'NoSuchEntity':
                    raise
                raise ArgumentError(
                    "cannot find manifest file(s) {0} in bucket '{1}'."
                    .format(",".join(manifest_keys), bucket))
            #Read manifest info from pipe...
            manifest = BundleManifest.read_from_fileobj(manifest_r,
                                                        self.args.get('privatekey'))
        self.log.debug('Returning Manifest for image:' + str(manifest.image_name))
        return manifest

    def _download_file_to_fileobj(self, bucket, key, fileobj, closefds=True):
        try:
            download_files(bucket=bucket,
                           keys=[key],
                           fileobj=fileobj,
                           opath=None,
                           service=self.service,
                           config=self.config)
        finally:
            if closefds and fileobj:
                fileobj.close()


    def _download_and_unbundle(self, bucket, manifest, outfile, debug=False):
        unbundle_r, unbundle_w = open_pipe_fileobjs()
        #setup progress bar...
        try:
            label = self.args.get('progressbar_label', 'Download -> UnBundling')
            pbar = self.get_progressbar(label=label,
                                        maxval=manifest.image_size)
        except NameError:
            pbar = None
            #Create the download process and unbundle pipeline...
        try:
            writer = spawn_process(self._download_parts,
                                   bucket=bucket,
                                   parts=manifest.image_parts,
                                   fileobj=unbundle_w,
                                   show_progress=False,
                                   close_fds=True)
            unbundle_w.close()
            waitpid_in_thread(writer.pid)
            digest = create_unbundle_pipeline(infile=unbundle_r,
                                              outfile=outfile,
                                              enc_key=manifest.enc_key,
                                              enc_iv=manifest.enc_iv,
                                              progressbar=pbar,
                                              debug=self.args.get('debug'),
                                              maxbytes=int(self.args['maxbytes']))

            digest = digest.strip()
            #Verify the Checksum return from the unbundle operation matches the manifest
            if digest != manifest.image_digest:
                raise ValueError('Digest mismatch. Extracted image appears to be corrupt '
                                 '(expected digest: {0}, actual: {1})'
                .format(manifest.image_digest, digest))
            self.log.debug("\nExpected digest:" + str(manifest.image_digest) + "\n" +
                           "  Actual digest:" + str(digest))
        except KeyboardInterrupt:
            print 'Caught keyboard interrupt'
            return
        finally:
            if unbundle_r:
                unbundle_r.close()
            if unbundle_w:
                unbundle_w.close()
        return digest


    def _download_parts(self,
                        bucket,
                        parts,
                        directory=None,
                        fileobj=None,
                        show_progress=True,
                        close_fds=False,
                        debug=False,
                        **kwargs):
        chunk_size = euca2ools.bundle.pipes._BUFSIZE
        if (not directory and not fileobj) or (directory and fileobj):
            raise ValueError('Must specify either directory or fileobj argument')
        try:
            for part in parts:
                self.log.debug('Downloading part:' + str(part.filename))

                #sha1sum = hashlib.sha1()
                #part_file_path = os.path.join(bucket, part.filename)
                #self.path = part_file_path
                #response = self.send()
                #for chunk in response.iter_content(chunk_size=chunk_size):
                #    sha1sum.update(chunk)
                #    fileobj.write(chunk)
                #    fileobj.flush()
                #part_digest = sha1sum.hexdigest()
                #self.log.debug("PART NUMBER:" + str(parts.index(part)) + "/" + str(len(parts)))
                #self.log.debug('Part sha1sum:' + str(part_digest))
                #self.log.debug('Expected sum:' + str(part.hexdigest))
                #if part_digest != part.hexdigest:
                #    raise ValueError('Input part file may be corrupt:{0} '.format(part.filename),
                #                     '(expected digest: {0}, actual: {1})'.format(part.hexdigest, part_digest))

                part_digest = download_files(bucket=bucket,
                                             keys=[part.filename],
                                             opath=directory,
                                             fileobj=fileobj,
                                             service=self.service,
                                             config=self.config,
                                             show_progress=show_progress
                                             )[os.path.join(bucket,part.filename)]
                self.log.debug("Part num:" + str(parts.index(part)) + "/" +
                               str(len(parts)))
                self.log.debug('Part sha1sum:' + str(part_digest))
                self.log.debug('Expected sum:' + str(part.hexdigest))
                if part_digest != part.hexdigest:
                    raise ValueError('Input part file may be corrupt:{0} '
                                     .format(part.filename),
                                     '(expected digest: {0}, actual: {1})'
                                     .format(part.hexdigest, part_digest))
        except IOError as ioe:
            # HACK
            self.log.debug('Error in _download_parts.' + str(ioe))
            if not debug:
                return
            raise ioe
        finally:
            if fileobj:
                fileobj.close()

    # noinspection PyExceptionInherit
    def main(self):
        directory = self.args.get('directory')
        bucket = self.args.get('bucket').split('/', 1)[0]
        self.log.debug('bucket:{0} directory:{1}'.format(bucket, directory))
        CheckBucket(bucket=bucket, service=self.service,
                    config=self.config).main()
        #Fetch and build a manifest obj from args provided...
        manifest = self._get_manifest_obj()

        #If a destination file was provided, download and unbundle to that file...
        if self.args.get('unbundle'):
            if directory == '-':
                fileobj = os.fdopen(os.dup(os.sys.stdin.fileno()))
            else:
                file_path = str(directory).rstrip('/') + "/" + manifest.image_name
                fileobj = open(file_path, 'w')
            try:
                self._download_and_unbundle(bucket=bucket,
                                            manifest=manifest,
                                            outfile=fileobj,
                                            debug=self.args.get('debug'))
            finally:
                if fileobj:
                    fileobj.close()
            if self.args.get('show_progress'):
                print "Bundle downloaded and unbundled to '{0}'".format(file_path)
        else:
            #If a directory was provided download the bundled parts to that directory...
            if not os.path.isdir(directory):
                raise ArgumentError(
                    "location '{0}' is either not a directory or does not exist."
                    .format(directory))
            self._download_parts(bucket=bucket,
                                 parts=manifest.image_parts,
                                 directory=directory,
                                 fileobj=None)
            if self.args.get('show_progress'):
                print "Bundle downloaded to dir '{0}'".format(directory)

if __name__ == '__main__':
    DownloadBundle.run()