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
from io import BytesIO
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
from euca2ools.bundle.manifest import BundleManifest
import euca2ools.bundle.pipes
from euca2ools.bundle.pipes.core import create_unbundle_pipeline
from euca2ools.commands.bundle.helpers import download_files, get_manifest_keys
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.checkbucket import CheckBucket
from euca2ools.exceptions import AWSError


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
                help='''The directory to download the parts to.''')]

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
        if isinstance(dest_dir, basestring):
            if not (dest_dir == "-"):
                dest_dir = os.path.expanduser(os.path.abspath(dest_dir))
                if not os.path.exists(dest_dir):
                    raise ArgumentError("Destination directory '{0}' "
                                        "does not exist"
                                        .format(dest_dir))
                if not os.path.isdir(dest_dir):
                    raise ArgumentError("Destination '{0}' is not Directory"
                                        .format(dest_dir))
        self.args['directory'] = dest_dir


    def _get_manifest_obj(self, private_key=None):
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
                manifest = BundleManifest.read_from_file(
                    manifest, private_key)
        else:
            #Read in remote manifest via multi-process...
            bucket = self.args.get('bucket')
            prefix = self.args.get('prefix')
            #Make sure the manifest exists, and the prefix is unique...
            self.log.debug('Getting manifest bucket "{0}" prefix "{1}"'
                           .format(bucket, prefix))
            manifest_keys = get_manifest_keys(bucket,
                                              prefix,
                                              service=self.service,
                                              config=self.config)
            if not manifest_keys:
                if prefix:
                    raise ArgumentError("no manifests found with prefix '{0}' "
                                        "in bucket '{1}'."
                                        .format(prefix, bucket))
                else:
                    raise ArgumentError("no manifests found in bucket '{0}'."
                                        .format(bucket))
            if len(manifest_keys) > 1:
                raise RuntimeError('Multiple manifests found:{0}'
                                   .format(",".join(str(m)
                                           for m in manifest_keys)))
            #Read the manifest into an obj...
            manifest_fileobj = BytesIO()
            manifest_key = manifest_keys.pop()
            try:
                download_files(bucket=bucket,
                               keys=[manifest_key],
                               fileobj=manifest_fileobj,
                               opath=None,
                               service=self.service,
                               config=self.config)
            except AWSError as err:
                if err.code != 'NoSuchEntity':
                    raise
                raise ArgumentError(
                    "cannot find manifest file(s) {0} in bucket '{1}'."
                    .format(",".join(manifest_keys), bucket))
            #Read manifest info from pipe...
            manifest = BundleManifest.read_from_fileobj(
                manifest_fileobj,private_key=private_key)
        self.log.debug('Returning Manifest for image:{0}'
                       .format(str(manifest.image_name)))
        return manifest

    def _download_parts(self,
                        bucket,
                        parts,
                        directory=None,
                        fileobj=None,
                        show_progress=True,
                        debug=False):
        if (not directory and not fileobj) or (directory and fileobj):
            raise ValueError('Must specify either directory'
                             ' or fileobj argument')
        try:
            for part in parts:
                self.log.debug('Downloading part:' + str(part.filename))
                part_dict = download_files(bucket=bucket,
                                           keys=[part.filename],
                                           opath=directory,
                                           fileobj=fileobj,
                                           service=self.service,
                                           config=self.config,
                                           show_progress=show_progress)
                part_digest = part_dict[os.path.join(bucket, part.filename)]
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
        fileobj = None
        dest_path = None
        bucket = self.args.get('bucket').split('/', 1)[0]
        self.log.debug('bucket:{0} directory:{1}'.format(bucket, directory))
        CheckBucket(bucket=bucket, service=self.service,
                    config=self.config).main()
        #Fetch and build a manifest obj from args provided...
        manifest = self._get_manifest_obj()

        #If directory is a file obj or "-"(stdout), download that fileobj...
        if isinstance(directory, basestring):
            if directory == '-':
                #Write bundle to stdout...
                fileobj = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
                self.args['show_progress'] = False
                directory = None
            else:
                #write bundle files to directory...
                if not os.path.isdir(directory):
                    raise ArgumentError(
                        "location '{0}' is either not a directory"
                        " or does not exist."
                        .format(directory))
                self.args['show_progress'] = True
                dest_path = directory
        else:
            #Assume the directory arg is a file obj to write bundle to
            fileobj = directory
            directory = None

        self._download_parts(bucket=bucket,
                             parts=manifest.image_parts,
                             directory=directory,
                             fileobj=fileobj,
                             show_progress=self.args.get('show_progress'),
                             debug=self.args.get('debug'))
        return dest_path

    def print_result(self, result):
        if result:
            print "Bundle downloaded to '{0}'".format(result)

if __name__ == '__main__':
    DownloadBundle.run()
