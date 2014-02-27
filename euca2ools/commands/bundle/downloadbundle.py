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
from euca2ools.commands.bundle.helpers import get_manifest_keys
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.getobject import GetObject
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
                    help='''Use a local bundle manifest file to specify bundle
                    to download'''),
                Arg('-p', '--prefix',
                    help='''Download the bundle that begins with a specific
                    prefix (e.g. "fry" for "fry.manifest.xml")''')),
            Arg('-d', '--directory', default=".",
                help='''The directory to download the bundle parts to.
                        Use "-" to download to stdout''')]

    # noinspection PyExceptionInherit
    def configure(self):
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

    def _get_manifest_obj(self, private_key=None, dest_dir=None):
        '''
        Attempts to return a BundleManifest obj based upon the provided
        DownloadBundle 'manifest' argument. If the arg is not a BundleManifest
        an attempt is made to retrieve the manifest from either a;
        local file path, remote bucket/prefix, or fileobj, whichever arg type
        is provided.
        :param private_key: Local file path to key used to create the bundle.
        :dest_dir: Local dir path. If provided, and manifest is to be
                   downloaded, the manifest will also be written to a file
                   in this directory.
        :returns: BundleManifest obj
        '''
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
                return BundleManifest.read_from_file(manifest, private_key)
        else:
            return self._download_manifest(bucket=self.args.get('bucket'),
                                           prefix=self.args.get('prefix'),
                                           private_key=private_key,
                                           dest_dir=dest_dir)

    def _download_manifest(self,
                           bucket=None,
                           prefix=None,
                           private_key=None,
                           dest_dir=None):
        '''
        Read in bundle manifest from remote bucket.
        :param bucket: Bucket to download bundle manifest from
        :param prefix: Manifest prefix used to download bundle
        :param private_key: Local file path to key used to create the bundle.
        :dest_dir: Local dir path. If provided the downloaded manifest will
                   be written to a file in this directory, otherwise it will
                   not be written to a local file.
        :returns: BundleManifest obj
        '''
        self.log.debug('download to dest_dir:' + str(dest_dir))
        bucket = bucket or self.args.get('bucket')
        prefix = prefix or self.args.get('prefix')
        if bucket is None or prefix is None:
            raise ArgumentError('Need to provide both bucket and prefix'
                                ' to download manifest')
        #Make sure the manifest exists, and the prefix is unique...
        self.log.debug('Downloading manifest bucket "{0}" prefix "{1}"'
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
        manifest_key = manifest_keys.pop()
        #Write to a local file if dest_dir was provided...
        if dest_dir:
            #Download paths to individual files under provided directory...
            if not os.path.isdir(dest_dir):
                self.log.debug('Creating dir at: {0}'.format(dest_dir))
                os.mkdir(dest_dir)
            local_file_path = os.path.join(dest_dir,
                                           os.path.basename(manifest_key))
            self.log.debug('Writing manifest to "{0}"'.format(local_file_path))
            manifest_fileobj = open(local_file_path, 'w+')
        else:
            manifest_fileobj = BytesIO()
        #Read manifest in from fileobj and create BundleManifest obj...
        with manifest_fileobj:
            try:
                path = os.path.join(bucket, manifest_key)
                self.log.debug('Attempting to download:{0}'.format(path))
                GetObject(paths=[path],
                          fileobj=manifest_fileobj,
                          opath=None,
                          service=self.service,
                          config=self.config).main()
            except AWSError as err:
                if err.code != 'NoSuchEntity':
                    raise
                raise ArgumentError(
                    "cannot find manifest file(s) {0} in bucket '{1}'."
                    .format(",".join(manifest_keys), bucket))
            #Read manifest info from pipe...
            manifest_fileobj.seek(0)
            manifest = BundleManifest.read_from_fileobj(
                manifest_fileobj, privkey_filename=private_key)
        manifest.manifest_key = manifest_key
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
        '''
        Attempts to download a list of parts to either the provided directory
        or fileobj. If a directory is provided, parts will be written to
        individual files within that directory. If a fileobj is provided, all
        parts will be concatenated/written to that fileobj.
        :param bucket: bucket containing the parts to be downloaded
        :param parts: list of parts to download
        :param directory: local directory to write parts to
        :param fileobj: fileobj to download and concatenate parts to
        :param show_progress: boolean to provide progressbar per part
        :param debug: boolean to determine exception handling of this method
        '''
        if (not directory and not fileobj) or (directory and fileobj):
            raise ValueError('Must specify either directory'
                             ' or fileobj argument')
        try:
            for part in parts:
                self.log.debug('Downloading part:' + str(part.filename))
                path = os.path.join(bucket, part.filename)
                part_dict = GetObject(paths=[path],
                                      opath=directory,
                                      fileobj=fileobj,
                                      service=self.service,
                                      config=self.config,
                                      show_progress=show_progress).main()
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
        destination_arg = self.args.get('directory')
        fileobj = None
        dest_path_str = None
        manifest_dest_dir = None
        bucket = self.args.get('bucket').split('/', 1)[0]
        self.log.debug('bucket:{0} directory:{1}'
                       .format(bucket, destination_arg))
        CheckBucket(bucket=bucket,
                    service=self.service,
                    config=self.config).main()
        #If destination is a fileobj or "-"(stdout), download to that fileobj
        if isinstance(destination_arg, basestring):
            if destination_arg == '-':
                #Write bundle to stdout...
                fileobj = os.fdopen(os.dup(os.sys.stdout.fileno()), 'w')
                self.args['show_progress'] = False
                directory = None
            else:
                #write bundle files to directory provided...
                if not os.path.isdir(destination_arg):
                    raise ArgumentError(
                        "location '{0}' is either not a directory"
                        " or does not exist."
                        .format(destination_arg))
                self.args['show_progress'] = True
                dest_path_str = destination_arg
                directory = destination_arg
                manifest_dest_dir = directory
        else:
            #Assume the destination is a file obj to write bundle to
            fileobj = destination_arg
            directory = None
        #Fetch and build a manifest obj from args provided...
        manifest = self._get_manifest_obj(dest_dir=manifest_dest_dir)
        #Download all parts from manifest to destination...
        self._download_parts(bucket=bucket,
                             parts=manifest.image_parts,
                             directory=directory,
                             fileobj=fileobj,
                             show_progress=self.args.get('show_progress'),
                             debug=self.args.get('debug'))
        return dest_path_str

    def print_result(self, result):
        if result:
            print "Bundle downloaded to '{0}'".format(result)

if __name__ == '__main__':
    DownloadBundle.run()
