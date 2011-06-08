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

import os
import euca2ools.commands.eucacommand
from boto.roboto.param import Param
import euca2ools.bundler
from euca2ools.exceptions import NotFoundError, CommandFailed

class BundleImage(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Bundles an image for use with Eucalyptus or Amazon EC2.'
    Options = [Param(name='image_path', short_name='i', long_name='image',
                     optional=False, ptype='file',
                     doc='Path to the image file to bundle.'),
               Param(name='user', short_name='u', long_name='user',
                     optional=True, ptype='string',
                     doc="""User ID (12-digit) of the user who is
                     bundling the image"""),
               Param(name='cert_path', short_name='c', long_name='cert',
                     optional=True, ptype='file',
                     doc='Path the users PEM-encoded certificate.'),
               Param(name='private_key_path',
                     short_name='k', long_name='privatekey',
                     optional=True, ptype='string',
                     doc='Path to users PEM-encoded private key.'),
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
                     optional=True, ptype='string',
                     doc="""Default block device mapping for the image
                     (comma-separated list of key=value pairs)."""),
               Param(name='destination',
                     short_name='d', long_name='destination',
                     optional=True, ptype='string', default='/tmp',
                     doc="""Directory to store the bundled image in.
                     Defaults to /tmp.  Recommended."""),
               Param(name='ec2cert_path', long_name='ec2cert',
                     optional=True, ptype='file',
                     doc="Path to the Cloud's X509 public key certificate."),
               Param(name='target_arch',
                     short_name='r', long_name='arch',
                     optional=True, ptype='string', default='x86_64',
                     doc="""Target architecture for the image
                     Valid values: i386 | x86_64."""),
               Param(name='batch', long_name='batch',
                     optional=True, ptype='boolean',
                     doc='Run in batch mode.  Compatibility only, has no effect')]

    def get_block_devs(self):
        mapping_str = self.block_device_mapping
        mapping = []
        mapping_pairs = mapping_str.split(',')
        for m in mapping_pairs:
            m_parts = m.split('=')
            if len(m_parts) > 1:
                mapping.append(m_parts[0])
                mapping.append(m_parts[1])
        return mapping

    def add_product_codes(self):
        product_codes = []
        product_code_values = self.product_codes.split(',')

        for p in product_code_values:
            product_codes.append(p)

        return product_codes

    def main(self):
        if self.cert_path is None:
            self.cert_path = self.get_environ('EC2_CERT')
        if self.private_key_path is None:
            self.private_key_path = self.get_environ('EC2_PRIVATE_KEY')
        if self.user is None:
            self.user = self.get_environ('EC2_USER_ID')
        if self.ec2cert_path is None:
            self.ec2cert_path = self.get_environ('EUCALYPTUS_CERT')
        
        bundler = euca2ools.bundler.Bundler(self)
        
        self.user = self.user.replace('-', '')

        image_size = bundler.check_image(self.image_path, self.destination)
        if not self.prefix:
            self.prefix = self.get_relative_filename(self.image_path)
        try:
            (tgz_file, sha_tar_digest) = bundler.tarzip_image(self.prefix,
                                                              self.image_path,
                                                              self.destination)
        except (NotFoundError, CommandFailed):
            sys.exit(1)

        (encrypted_file, key, iv, bundled_size) = bundler.encrypt_image(tgz_file)
        os.remove(tgz_file)
        (parts, parts_digest) = bundler.split_image(encrypted_file)
        if self.block_device_mapping:
            self.block_device_mapping = self.get_block_devs()
        if self.product_codes:
            self.product_codes = self.add_product_codes(self.product_codes)
        bundler.generate_manifest(self.destination, self.prefix,
                                  parts, parts_digest,
                                  self.image_path, key, iv,
                                  self.cert_path, self.ec2cert_path,
                                  self.private_key_path,
                                  self.target_arch, image_size,
                                  bundled_size, sha_tar_digest,
                                  self.user, self.kernel_id, self.ramdisk_id,
                                  self.block_device_mapping, self.product_codes)
        os.remove(encrypted_file)

    main_cli = main

