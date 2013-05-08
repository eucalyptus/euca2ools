# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

from euca2ools.commands.bundle.helpers import download_files
from euca2ools.commands.bundle.helpers import get_manifest_keys
from euca2ools.commands.bundle.helpers import get_manifest_parts
from euca2ools.commands.walrus import WalrusRequest
from euca2ools.commands.walrus.checkbucket import CheckBucket
from euca2ools.exceptions import AWSError
import os
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
import shutil
import sys
import tempfile


class DownloadBundle(WalrusRequest):
    DESCRIPTION = 'Downloads a bundled image from a bucket.'
    ARGS = [Arg('-b', '--bucket', metavar='BUCKET', required=True,
                help='Name of the bucket to upload to.'),
            MutuallyExclusiveArgList(
                Arg('-m', '--manifest', dest='manifest_path', metavar='FILE',
                    help='Path to local manifest file for bundled image.'),
                Arg('-p', '--prefix', metavar='PREFIX',
                    help='Prefix used to identify the image in the bucket')),
            Arg('-d', '--directory', metavar='DIRECTORY',
                help='The directory to download the parts to.')]

    def _download_parts(self, manifests, directory):
        bucket = self.args.get('bucket')
        for manifest in manifests:
            parts = get_manifest_parts(os.path.join(directory, manifest))
            download_files(bucket, parts, directory, service=self.service,
                           config=self.config,
                           show_progress=self.args.get('show_progress', True))

    def _download_by_local_manifest(self, directory):
        manifest_path = self.args.get('manifest_path')
        if not os.path.isfile(manifest_path):
            raise ArgumentError(
                "manifest file '{0}' does not exist.".format(manifest_path))
        manifest_key = os.path.basename(manifest_path)
        if not os.path.exists(os.path.join(directory, manifest_key)):
            shutil.copy(manifest_path, directory)
        self._download_parts([manifest_key], directory)

    def _download_by_prefix(self, directory):
        bucket = self.args.get('bucket')
        prefix = self.args.get('prefix')
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
        try:
            download_files(bucket, manifest_keys, directory,
                           service=self.service, config=self.config,
                           show_progress=self.args.get('show_progress', True))
        except AWSError as err:
            if err.code != 'NoSuchEntity':
                raise
            raise ArgumentError(
                "cannot find manifest file(s) {0} in bucket '{1}'."
                .format(",".join(manifest_keys), bucket))
        self._download_parts(manifest_keys, directory)

    def main(self):
        bucket = self.args.get('bucket')
        CheckBucket(bucket=bucket, service=self.service,
                    config=self.config).main()

        directory = self.args.get('directory') or tempfile.mkdtemp()
        if not os.path.isdir(directory):
            raise ArgumentError(
                "location '{0}' is either not a directory or does not exist."
                .format(directory))

        if self.args.get('manifest_path'):
            self._download_by_local_manifest(directory)
        else:
            self._download_by_prefix(directory)

        # Print location if we used a temp directory
        if not self.args.get('directory'):
            print >> sys.stderr, "Bundle downloaded to '{0}'".format(directory)
