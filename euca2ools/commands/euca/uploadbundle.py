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
from boto.s3.connection import Location

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
                     doc='Do not  upload the manifest.'),
               Param(name='location', long_name='location',
                     optional=True, ptype='string', default=Location.DEFAULT,
                     doc="""The location of the destination S3 bucket
                            Valid values: US|EU|us-west-1|ap-southeast-1|ap-northeast-1""")]

    def ensure_bucket(self, acl, location=Location.DEFAULT):
        bucket_instance = None
        s3conn = self.make_connection_cli('s3')
        try:
            print 'Checking bucket:', self.bucket
            bucket_instance = s3conn.get_bucket(self.bucket)
            if location:
                if location != bucket_instance.get_location():
                    msg = 'Supplied location does not match bucket location'
                    self.display_error_and_exit(msg)
        except S3ResponseError, s3error:
            s3error_string = '%s' % s3error
            if s3error_string.find('404') >= 0:
                try:
                    print 'Creating bucket:', self.bucket
                    bucket_instance = s3conn.create_bucket(self.bucket,
                                                           policy=acl,
                                                           location=location)
                except S3CreateError:
                    msg = 'Unable to create bucket %s' % self.bucket
                    self.display_error_and_exit(msg)
            elif s3error_string.find('403') >= 0:
                msg = 'You do not have permission to access bucket:', self.bucket
                self.display_error_and_exit(msg)
            else:
                self.display_error_and_exit(s3error_string)
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
                        canned_acl=None, upload_policy=None,
                        upload_policy_signature=None):
        print 'Uploading manifest file'
        k = Key(bucket_instance)
        k.key = self.get_relative_filename(manifest_filename)
        manifest_file = open(manifest_filename, 'rb')
        headers = {}
        if upload_policy:
            headers['S3UploadPolicy'] = upload_policy
        if upload_policy_signature:
            headers['S3UploadPolicySignature']=upload_policy_signature

        try:
            k.set_contents_from_file(manifest_file, policy=canned_acl,
                                     headers=headers)
        except S3ResponseError, s3error:
            s3error_string = '%s' % s3error
            if s3error_string.find('403') >= 0:
                msg = 'Permission denied while writing:', k.key
            else:
                msg = s3error_string
            self.display_error_and_exit(msg)

    def upload_parts(self, bucket_instance, directory, parts,
                     part_to_start_from, canned_acl=None,
                     upload_policy=None, upload_policy_signature=None):
        if part_to_start_from:
            okay_to_upload = False
        else:
            okay_to_upload = True

        headers = {}
        if upload_policy:
            headers['S3UploadPolicy'] = upload_policy
        if upload_policy_signature:
            headers['S3UploadPolicySignature']=upload_policy_signature

        for part in parts:
            if part == part_to_start_from:
                okay_to_upload = True
            if okay_to_upload:
                print 'Uploading part:', part
                k = Key(bucket_instance)
                k.key = part
                part_file = open(os.path.join(directory, part), 'rb')
                try:
                    k.set_contents_from_file(part_file, policy=canned_acl,
                                             headers=headers)
                except S3ResponseError, s3error:
                    s3error_string = '%s' % s3error
                    if s3error_string.find('403') >= 0:
                        msg = 'Permission denied while writing:', k.key
                    else:
                        msg = s3error_string
                    self.display_error_and_exit(msg)

    def main(self):
        bucket_instance = self.ensure_bucket(self.canned_acl, self.location)
        parts = self.get_parts(self.manifest_path)
        manifest_directory, manifest_file = os.path.split(self.manifest_path)
        if not self.bundle_path:
            self.bundle_path = manifest_directory
        if not self.skip_manifest and not self.part:
            self.upload_manifest(bucket_instance, self.manifest_path,
                                 self.canned_acl)
        self.upload_parts(bucket_instance, self.bundle_path,
                          parts, self.part, self.canned_acl)
        print 'Uploaded image as %s/%s' % (self.bucket,
                self.get_relative_filename(self.manifest_path))

    def main_cli(self):
        self.main()


