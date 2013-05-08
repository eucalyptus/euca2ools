# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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
from euca2ools.commands.walrus.deletebucket import DeleteBucket
from euca2ools.commands.walrus.deleteobject import DeleteObject
from euca2ools.commands.walrus.getobject import GetObject
from euca2ools.commands.walrus.listbucket import ListBucket
from euca2ools.exceptions import AWSError
from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.exceptions import ArgumentError
import argparse
import os
import shutil
import sys
import tempfile
import time
from xml.dom import minidom


class DeleteBundle(WalrusRequest):
    DESCRIPTION = 'Delete a previously-uploaded bundle.'
    ARGS = [Arg('-b', '--bucket', dest='bucket', metavar='BUCKET',
                required=True, help='Name of the bucket to delete from.'),
            MutuallyExclusiveArgList(True,
                Arg('-m', '--manifest', dest='manifest_path', metavar='MANIFEST',
                    help='Delete a bundle based on a local manifest file'),
                Arg('-p', '--prefix', dest='prefix',
                    help=('Delete a bundle with a manifest in the bucket that '
                        'begins with a specific name  (e.g. "fry" for '
                        '"fry.manifest.xml")')),
                Arg('--delete-all-bundles', dest='delete_all',
                    action='store_true', help=argparse.SUPPRESS)),
            Arg('--clear', dest='clear', action='store_true',
                help='Delete the entire bucket if possible')]

    def _delete_manifest_parts(self, manifest_keys, directory):
        bucket = self.args.get('bucket')
        for key in manifest_keys:
            paths = get_manifest_parts(os.path.join(directory, key), bucket)
            DeleteObject(paths=paths, service=self.service,
                         config=self.config).main()

    def _delete_manifest_keys(self, manifest_keys):
        bucket = self.args.get('bucket')
        paths = [os.path.join(bucket, key) for key in manifest_keys]
        DeleteObject(paths=paths).main()

    def _delete_by_local_manifest(self):
        manifest_path = self.args.get('manifest_path')
        if not os.path.isfile(manifest_path):
            raise ArgumentError("manifest file '%s' does not exist." % manifest_path)
        manifest_keys = [os.path.basename(manifest_path)]
        directory = os.path.dirname(manifest_path) or '.'
        # When we use a local manifest file, we should still check if there is
        # a matching manifest in the bucket. If it's there then we delete it.
        # It's okay if this fails. It might not be there.
        try:
            self._delete_manifest_keys(manifest_keys)
        except AWSError as err:
            if err[2] == 'NoSuchEntity':
                pass
            else:
                raise
        self._delete_manifest_parts(manifest_keys, directory)

    def _delete_by_prefix(self):
        bucket = self.args.get('bucket')
        directory = tempfile.mkdtemp()
        try:
            manifest_keys = ['%s.manifest.xml' % self.args.get('prefix')]
            try:
                download_files(bucket, manifest_keys, directory,
                               service=self.service, config=self.config)
            except AWSError as err:
                if err[2] == 'NoSuchEntity':
                    raise ArgumentError("manifest file '%s' does not exist in "
                                        "bucket '%s'."
                                        % (manifest_keys[0], bucket))
                else:
                    raise
            self._delete_manifest_parts(manifest_keys, directory)
            self._delete_manifest_keys(manifest_keys)
        finally:
            shutil.rmtree(directory)

    def _delete_all_bundles(self):
        bucket = self.args.get('bucket')
        print >> sys.stderr, """All bundles in bucket '%s' will be deleted.
If this is not what you want, press Ctrl+C in the next 10 seconds""" % bucket
        try:
            for _ in range(10):
                sys.stderr.write('.')
                sys.stderr.flush()
                time.sleep(1)
        except KeyboardInterrupt:
            print >> sys.stderr
            print >> sys.stderr, 'Bundle deletion canceled by user.'
            sys.exit(1)
        finally:
            sys.stderr.write('\n')
            sys.stderr.flush()

        directory = tempfile.mkdtemp()
        try:
            manifest_keys = get_manifest_keys(bucket, service=self.service,
                                              config=self.config)
            download_files(bucket, manifest_keys, directory,
                           service=self.service, config=self.config)
            self._delete_manifest_parts(manifest_keys, directory)
            self._delete_manifest_keys(manifest_keys)
        finally:
            shutil.rmtree(directory)

    def main(self):
        bucket = self.args.get('bucket')

        # Verify bucket existence
        CheckBucket(bucket=bucket, service=self.service,
                    config=self.config).main()

        # Use local manifest file
        if self.args.get('manifest_path'):
            self._delete_by_local_manifest()
        # Use manifest file in walrus
        elif self.args.get('prefix'):
            self._delete_by_prefix()
        # Delete all bundles in the bucket
        elif self.args.get('delete_all') is True:
            self._delete_all_bundles()

        if self.args.get('clear') is True:
            DeleteBucket(bucket=bucket, service=self.service,
                         config=self.config).main()
