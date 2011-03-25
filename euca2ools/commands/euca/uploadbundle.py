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

class UploadBundle(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Upload a previously bundled image to the cloud.'
    Options = [Param(name='bucket', short_name='b', long_name='bucket',
                     optional=False, ptype='string',
                     doc='Name of the bucket to upload to.'),
               Param(name='manifest_path',
                     short_name='m', long_name='manifest',
                     optional=False, ptype='file',
                     doc='Path to the manifest file for bundled image.'),
               Param(name='canned_acl',  long_name='acl',
                     optional=True, ptype='string', default='aws-exec-read',
                     doc='Canned access policy'),
               Param(name='ec2cert_path', long_name='ec2cert',
                     optional=True, ptype='file',
                     doc="Path to the Cloud's X509 public key certificate."),
               Param(name='bundle_path',
                     short_name='d', long_name='directory',
                     optional=True, ptype='string',
                     doc="""The directory containing the bundled
                     image to upload (defaults to the manifest directory)."""),
               Param(name='part', long_name='part',
                     optional=True, ptype='integer',
                     doc='Uploads specified part and all subsequent parts.'),
               Param(name='skip_manifest', long_name='skipmanifest',
                     optional=True, ptype='boolean', default=False,
                     doc='Do not  upload the manifest.')]

    def ensure_bucket(self, bucket, canned_acl=None):
        bucket_instance = None
        s3conn = self.make_connection_cli('s3')
        try:
            print 'Checking bucket:', bucket
            bucket_instance = s3conn.get_bucket(bucket)
        except S3ResponseError, s3error:
            s3error_string = '%s' % s3error
            if s3error_string.find('404') >= 0:
                try:
                    print 'Creating bucket:', bucket
                    bucket_instance = s3conn.create_bucket(bucket,
                                                           policy=canned_acl)
                except S3CreateError:
                    print 'Unable to create bucket %s' % bucket
                    sys.exit()
            elif s3error_string.find('403') >= 0:
                print 'You do not have permission to access bucket:', bucket
                sys.exit()
            else:
                print s3error_string
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

    def upload_manifest(self, bucket_instance, manifest_filename,
                        canned_acl=None):
        print 'Uploading manifest file'
        k = Key(bucket_instance)
        k.key = self.get_relative_filename(manifest_filename)
        manifest_file = open(manifest_filename, 'rb')
        try:
            k.set_contents_from_file(manifest_file, policy=canned_acl)
        except S3ResponseError, s3error:
            s3error_string = '%s' % s3error
            if s3error_string.find('403') >= 0:
                print 'Permission denied while writing:', k.key
            else:
                print s3error_string
            sys.exit()

    def upload_parts(self, bucket_instance, directory, parts,
                     part_to_start_from, canned_acl=None):
        if part_to_start_from:
            okay_to_upload = False
        else:
            okay_to_upload = True

        for part in parts:
            if part == part_to_start_from:
                okay_to_upload = True
            if okay_to_upload:
                print 'Uploading part:', part
                k = Key(bucket_instance)
                k.key = part
                part_file = open(os.path.join(directory, part), 'rb')
                try:
                    k.set_contents_from_file(part_file, policy=canned_acl)
                except S3ResponseError, s3error:
                    s3error_string = '%s' % s3error
                    if s3error_string.find('403') >= 0:
                        print 'Permission denied while writing:', k.key
                    else:
                        print s3error_string
                    sys.exit()

    def main(self):
        bucket = self.options['bucket']
        manifest_path = self.options['manifest_path']
        ec2cert_path = self.options.get('ec2cert_path', None)
        directory = self.options.get('bundle_path', None)
        part = self.options.get('part', None)
        canned_acl = self.options.get('canned_acl', 'aws-exec-read')
        skipmanifest = self.options.get('skipmanifest', False)
        debug = False
        
        bucket_instance = self.ensure_bucket(self.bucket, self.canned_acl)
        parts = self.get_parts(self.manifest_path)
        manifest_directory, manifest_file = os.path.split(self.manifest_path)
        if not self.directory:
            self.directory = manifest_directory
        if not self.skipmanifest and not part:
            self.upload_manifest(bucket_instance, self.manifest_path,
                                 self.canned_acl)
        self.upload_parts(bucket_instance, self.directory,
                          parts, self.part, self.canned_acl)
        print 'Uploaded image as %s/%s' % (bucket,
                self.get_relative_filename(self.manifest_path))

    def main_cli(self):
        self.main()


