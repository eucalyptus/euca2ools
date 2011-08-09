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

import euca2ools.commands.eucacommand
from boto.roboto.param import Param
import sys
import os
from xml.dom import minidom
from boto.exception import S3ResponseError, S3CreateError
from boto.s3.key import Key

class DeleteBundle(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Delete a previously uploaded bundle.'
    Options = [Param(name='bucket', short_name='b', long_name='bucket',
                     optional=False, ptype='string',
                     doc='Name of the bucket to upload to.'),
               Param(name='manifest_path',
                     short_name='m', long_name='manifest',
                     optional=True, ptype='file',
                     doc='Path to the manifest file.'),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=True, ptype='string',
                     doc="""The filename prefix for bundled files.
                     Defaults to image name."""),
               Param(name='clear', long_name='clear',
                     optional=True, ptype='boolean', default=False,
                     doc='Delete the bucket containing the image.')]

    def ensure_bucket(self, bucket):
        bucket_instance = None
        s3conn = self.make_connection_cli('s3')
        try:
            bucket_instance = s3conn.get_bucket(bucket)
        except S3ResponseError, s3error:
            print 'Unable to get bucket %s' % bucket
            sys.exit()
        return bucket_instance

    def get_parts(self, manifest_filename):
        parts = []
        try:
            dom = minidom.parse(manifest_filename)
            manifest_elem = dom.getElementsByTagName('manifest')[0]
            parts_list = manifest_elem.getElementsByTagName('filename')
            for part_elem in parts_list:
                nodes = part_elem.childNodes
                for node in nodes:
                    if node.nodeType == node.TEXT_NODE:
                        parts.append(node.data)
        except:
            print 'problem parsing: %s' % manifest_filename
        return parts

    def get_manifests(self, bucket):
        manifests = []
        keys = bucket.get_all_keys()
        for k in keys:
            if k.name:
                if k.name.find('manifest') >= 0:
                    manifests.append(k.name)
        return manifests

    def download_manifests(self, bucket, manifests, directory):
        if len(manifests) > 0:
            if not os.path.exists(directory):
                os.makedirs(directory)
        for manifest in manifests:
            k = Key(bucket)
            k.key = manifest
            manifest_filename = os.path.join(directory, manifest)
            manifest_file = open(manifest_filename, 'wb')
            try:
                k.get_contents_to_file(manifest_file)
            except S3ResponseError, s3error:
                s3error_string = '%s' % s3error
                if s3error_string.find('200') < 0:
                    print s3error_string
                    print 'unable to download manifest %s' % manifest
                    if os.path.exists(manifest_filename):
                        os.remove(manifest_filename)
                    return False
            manifest_file.close()
        return True

    def delete_parts(self, bucket, manifests, directory=None):
        for manifest in manifests:
            manifest_filename = os.path.join(directory, manifest)
            parts = self.get_parts(manifest_filename)
            for part in parts:
                k = Key(bucket)
                k.key = part
                try:
                    k.delete()
                except S3ResponseError, s3error:
                    s3error_string = '%s' % s3error
                    if s3error_string.find('200') < 0:
                        print s3error_string
                        print 'unable to delete part %s' % part
                        sys.exit()


    def delete_manifests(self, bucket, manifests, clear, bucket_name):
        for manifest in manifests:
            k = Key(bucket)
            k.key = manifest
            try:
                k.delete()
            except Exception, s3error:
                s3error_string = '%s' % s3error
                if s3error_string.find('200') < 0:
                    print s3error_string
                    print 'unable to delete manifest %s' % manifest
                    try:
                        bucket = self.ensure_bucket(bucket_name)
                    except ConnectionFailed, e:
                        print e.message
                        sys.exit(1)
        if clear:
            try:
                bucket.delete()
            except Exception, s3error:
                s3error_string = '%s' % s3error
                if s3error_string.find('200') < 0:
                    print s3error_string
                    print 'unable to delete bucket %s' % bucket.name

    def remove_manifests(self, manifests, directory):
        for manifest in manifests:
            manifest_filename = os.path.join(directory, manifest)
            if os.path.exists(manifest_filename):
                os.remove(manifest_filename)

    def main(self):
        directory = os.path.abspath('/tmp')

        if not self.manifest_path and not self.prefix:
            print 'Neither manifestpath nor prefix was specified.'
            print 'All manifest data in bucket will be deleted.'

        bucket_instance = self.ensure_bucket(self.bucket)
        manifests = None
        delete_local_manifests = True
        if not self.manifest_path:
            if not self.prefix:
                manifests = self.get_manifests(bucket_instance)
            else:
                manifests = ['%s.manifest.xml' % self.prefix]
        else:
            manifests = ['%s'
                         % self.get_relative_filename(self.manifest_path)]
            directory = '%s' % self.get_file_path(self.manifest_path)
            delete_local_manifests = False
        return_code = self.download_manifests(bucket_instance, manifests,
                                              directory)
        if return_code:
            self.delete_parts(bucket_instance, manifests, directory)
        self.delete_manifests(bucket_instance, manifests,
                              self.clear, self.bucket)
        if delete_local_manifests:
            self.remove_manifests(manifests, directory)

    def main_cli(self):
        self.main()
