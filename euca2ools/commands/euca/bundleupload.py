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

import sys
import os
import euca2ools.commands.eucacommand
from boto.roboto.param import Param
from boto.exception import S3ResponseError, S3CreateError
from euca2ools.commands.euca.uploadbundle import UploadBundle
from euca2ools.commands.euca.bundleimage import BundleImage
import euca2ools.bundler
from euca2ools.exceptions import NotFoundError, CommandFailed

class BundleUpload(UploadBundle, BundleImage):

    Description = """Bundles an image and uploads on behalf of user.
                     NOTE: For use by the Eucalyptus Node Controller only"""
    
    Options = [Param(name='bucket', short_name='b', long_name='bucket',
                     optional=False, ptype='string',
                     doc='Name of the bucket to upload to.'),
               Param(name='image_path', short_name='i', long_name='image',
                     optional=False, ptype='file',
                     doc='The path to the image file to bundle'),
               Param(name='user', short_name='u', long_name='user',
                     optional=True, ptype='string',
                     doc='ID of the user doing the bundling'),
               Param(name='directory', short_name='d', long_name='directory',
                     optional=True, ptype='string', default='/tmp',
                     doc='Working directory where bundle should be generated'),
               Param(name='policy', short_name='c', long_name='policy',
                     optional=True, ptype='string',
                     doc='Base64 encoded S3 upload policy'),
               Param(name='policy_signature',
                     long_name='policysignature',
                     optional=True, ptype='string',
                     doc='Signature for the upload policy'),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=True, ptype='string',
                     doc="""The prefix for the bundle image files.
                     (default: image name)."""),
               Param(name='kernel_id', long_name='kernel',
                     optional=True, ptype='string',
                     doc='ID of the kernel to be associated with the image.'),
               Param(name='ramdisk_id', long_name='ramdisk',
                     optional=True, ptype='string',
                     doc='ID of the ramdisk to be associated with the image.'),
               Param(name='product_codes', long_name='product-codes',
                     optional=True, ptype='string',
                     doc='Product code to be associated with the image.'),
               Param(name='block_device_mapping',
                     short_name='b', long_name='block-device-mapping',
                     optional=True, ptype='string', cardinality='*',
                     doc="""Default block device mapping for the image
                     (comma-separated list of key=value pairs)."""),
               Param(name='target_arch',
                     short_name='r', long_name='arch',
                     optional=True, ptype='string', default='x86_64',
                     doc="""Target architecture for the image
                     Valid values: i386 | x86_64."""),
               Param(name='acl', long_name='acl',
                     optional=True, ptype='string', default='ec2-bundle-read',
                     doc='Canned ACL policy')]

    def main(self):
        self.cert_path = self.get_environ('EC2_CERT')
        self.ec2cert_path = self.get_environ('EUCALYPTUS_CERT')
        if self.user is None:
            self.user = self.get_environ('EC2_USER_ID')

        bundler = euca2ools.bundler.Bundler(self)
        image_size = bundler.check_image(self.image_path, self.directory)
        if not self.prefix:
            self.prefix = self.get_relative_filename(self.image_path)
        try:
            tgz_file, sha_tar_digest = bundler.tarzip_image(self.prefix,
                                                            self.image_path,
                                                            self.directory)
        except (NotFoundError, CommandFailed):
            sys.exit(1)

        encrypted_file, key, iv, bundled_size = bundler.encrypt_image(tgz_file)
        os.remove(tgz_file)
        parts, parts_digest = bundler.split_image(encrypted_file)
        if self.block_device_mapping:
            self.block_device_mapping = self.get_block_devs()
        if self.product_codes:
            self.product_codes = self.add_product_codes(self.product_codes)
        manifest_path = bundler.generate_manifest(self.directory,
                                                  self.prefix,
                                                  parts, parts_digest,
                                                  self.image_path, key, iv,
                                                  self.cert_path,
                                                  self.ec2cert_path,
                                                  None, self.target_arch,
                                                  image_size, bundled_size,
                                                  sha_tar_digest,
                                                  self.user, self.kernel_id,
                                                  self.ramdisk_id,
                                                  self.block_device_mapping,
                                                  self.product_codes)
        os.remove(encrypted_file)
            
        bucket_instance = self.ensure_bucket(self.acl)
        parts = self.get_parts(manifest_path)
        manifest_directory, manifest_file = os.path.split(manifest_path)
        if not self.directory:
            self.directory = manifest_directory
        # TODO: Since Walrus does not fully support S3 policies
        #       we are going to simply ignore the policy for now.
        self.upload_manifest(bucket_instance, manifest_path, self.acl,
                             self.policy, self.policy_signature)
        self.upload_parts(bucket_instance, self.directory, parts,
                          None, self.acl, self.policy, self.policy_signature)
        manifest_path = self.get_relative_filename(manifest_path)
        print "Uploaded image as %s/%s" % (self.bucket, manifest_path)
        bucket_instance.connection.make_request(bucket=self.bucket,
                                                key=manifest_path,
                                                action='ValidateImage')
        print 'Validated manifest %s/%s' % (self.bucket, manifest_path)
 
    def main_cli(self):
        self.main()
