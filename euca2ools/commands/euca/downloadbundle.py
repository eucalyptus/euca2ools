# Software License Agreement (BSD License)
#
# Copyright (c) 20092011, Eucalyptus Systems, Inc.
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

class DownloadBundle(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Downloads a bundled image from a bucket.'
    Options = [Param(name='bucket', short_name='b', long_name='bucket',
                     optional=False, ptype='string',
                     doc='Name of the bucket to upload to.'),
               Param(name='manifest_path',
                     short_name='m', long_name='manifest',
                     optional=True, ptype='string',
                     doc='Path to the manifest file for bundled image.'),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=True, ptype='string',
                     doc='Prefix used to identify the image in the bucket'),
               Param(name='directory',
                     short_name='d', long_name='directory',
                     optional=True, ptype='dir', default='/tmp',
                     doc='The directory to download the parts to.')]

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
        dom = minidom.parse(manifest_filename)
        manifest_elem = dom.getElementsByTagName('manifest')[0]
        parts_list = manifest_elem.getElementsByTagName('filename')
        for part_elem in parts_list:
            nodes = part_elem.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    parts.append(node.data)
        return parts

    def get_manifests(self, bucket, image_prefix=None):
        manifests = []
        keys = bucket.get_all_keys()
        for k in keys:
            if k.name:
                if k.name.find('manifest') >= 0:
                    if image_prefix:
                        if k.name.startswith(image_prefix):
                            manifests.append(k.name)
                    else:
                        manifests.append(k.name)
        return manifests

    def download_manifests(self, bucket, manifests, directory):
        if len(manifests) > 0:
            if not os.path.exists(directory):
                os.makedirs(directory)
        for manifest in manifests:
            k = Key(bucket)
            k.key = manifest
            print 'Downloading', manifest
            manifest_file = open(os.path.join(directory, manifest), 'wb')
            k.get_contents_to_file(manifest_file)
            manifest_file.close()

    def download_parts(self, bucket, manifests, directory):
        for manifest in manifests:
            manifest_filename = os.path.join(directory, manifest)
            parts = get_parts(manifest_filename)
            for part in parts:
                k = Key(bucket)
                k.key = part
                print 'Downloading', part
                part_file = open(os.path.join(directory, part), 'wb')
                k.get_contents_to_file(part_file)
                part_file.close()

    def main(self):
        bucket_instance = self.ensure_bucket(self.bucket)
        manifests = self.get_manifests(bucket_instance, self.prefix)
        self.download_manifests(bucket_instance, manifests, self.directory)
        self.download_parts(bucket_instance, manifests, self.directory)

    def main_cli(self):
        self.main()
