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

import os
import sys
import platform
import euca2ools.commands.eucacommand
from boto.roboto.param import Param
import euca2ools.bundler
import euca2ools.metadata
from euca2ools.exceptions import *

MAX_IMAGE_SIZE = 1024 * 10

class BundleVol(euca2ools.commands.eucacommand.EucaCommand):

    Description = 'Bundles an image for use with Eucalyptus or Amazon EC2.'
    Options = [Param(name='size', short_name='s', long_name='size',
                     optional=True, ptype='integer', default=MAX_IMAGE_SIZE,
                     doc='Size of the image in MB'),
               Param(name='user', short_name='u', long_name='user',
                     optional=True, ptype='string',
                     doc="""User ID (12-digit) of the user who is
                     bundling the image"""),
               Param(name='cert_path', short_name='c', long_name='cert',
                     optional=True, ptype='file',
                     doc='Path the users PEM-encoded certificate.'),
               Param(name='private_key_path',
                     short_name='k', long_name='privatekey',
                     optional=True, ptype='file',
                     doc='Path to users PEM-encoded private key.'),
               Param(name='all', short_name='a', long_name='all',
                     optional=True, ptype='boolean', default=False,
                     doc="""Bundle all directories (including
                     mounted filesystems."""),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=True, ptype='string', default='image',
                     doc="""The prefix for the bundle image files.
                     (default: image name)."""),
               Param(name='no_inherit',  long_name='no-inherit',
                     optional=True, ptype='boolean', default=True,
                     doc='Do not add instance metadata to the bundled image.'),
               Param(name='exclude',  short_name='e', long_name='exclude',
                     optional=True, ptype='string', default='',
                     doc='Comma-separated list of directories to exclude.'),
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
               Param(name='destination_path',
                     short_name='d', long_name='destination',
                     optional=True, ptype='string', default='/disk1',
                     doc="""Directory to store the bundled image in.
                     Defaults to /tmp.  Recommended."""),
               Param(name='ec2cert_path', long_name='ec2cert',
                     optional=True, ptype='file',
                     doc="Path to the Cloud's X509 public key certificate."),
               Param(name='target_architecture',
                     short_name='r', long_name='arch',
                     optional=True, ptype='string', default='x86_64',
                     doc="""Target architecture for the image
                     Valid values: i386 | x86_64."""),
               Param(name='volume_path', long_name='volume',
                     optional=True, ptype='dir', default='/',
                     doc='Path to mounted volume to bundle.'),
               Param(name='fstab_path', long_name='fstab',
                     optional=True, ptype='file',
                     doc='Path to the fstab to be bundled with image.'),
               Param(name='generate_fstab', long_name='generate-fstab',
                     optional=True, ptype='boolean', default=False,
                     doc='Generate fstab to bundle in image.'),
               Param(name='batch', long_name='batch',
                     optional=True, ptype='boolean',
                     doc='Run in batch mode.  For compatibility has no effect')]

    def check_root(self):
        if os.geteuid() == 0:
            return
        else:
            print 'Must be superuser to execute this command.'
            sys.exit()

    def check_image_size(self, size):
        if size > MAX_IMAGE_SIZE:
            msg = 'Image Size is too large (Max = %d MB)' % MAX_IMAGE_SIZE
            self.display_error_and_exit(msg)

    def parse_excludes(self, excludes_string):
        excludes = []
        if excludes_string:
            excludes_string = excludes_string.replace(' ', '')
            excludes = excludes_string.split(',')
        return excludes

    def get_instance_metadata(self, ramdisk_id, kernel_id, block_dev_mapping):
        md = euca2ools.metadata.MetaData()
        product_codes = None
        ancestor_ami_ids = None
        try:
            if not ramdisk_id:
                try:
                    ramdisk_id = md.get_instance_ramdisk()
                except MetadataReadError:
                    print 'Unable to read ramdisk id'

            if not kernel_id:
                try:
                    kernel_id = md.get_instance_kernel()
                except MetadataReadError:
                    print 'Unable to read kernel id'

            if not block_dev_mapping:
                try:
                    block_dev_mapping = \
                        md.get_instance_block_device_mappings()
                except MetadataReadError:
                    print 'Unable to read block device mapping'

            try:
                product_codes = md.get_instance_product_codes().split('\n'
                        )
            except MetadataReadError:
                print 'Unable to read product codes'

            try:
                ancestor_ami_ids = md.get_ancestor_ami_ids().split('\n')
            except MetadataReadError:
                print 'Unable to read ancestor ids'
        except IOError:

            print 'Unable to read instance metadata. Pass the --no-inherit option if you wish to exclude instance metadata.'
            sys.exit()

        return (ramdisk_id, kernel_id, block_dev_mapping, product_codes,
                ancestor_ami_ids)


    def add_product_codes(self, product_code_string, product_codes):
        if not product_codes:
            product_codes = []
        product_code_values = product_code_string.split(',')

        for p in product_code_values:
            product_codes.append(p)

        return product_codes

    def cleanup(self, path):
        if os.path.exists(path):
            os.remove(path)

    def get_block_devs(self, mapping_str):
        mapping = []
        mapping_pairs = mapping_str.split(',')
        for m in mapping_pairs:
            m_parts = m.split('=')
            if len(m_parts) > 1:
                mapping.append(m_parts[0])
                mapping.append(m_parts[1])
        return mapping

    def main(self):
        ancestor_ami_ids = None
        if self.cert_path is None:
            self.cert_path = self.get_environ('EC2_CERT')
        if self.private_key_path is None:
            self.private_key_path = self.get_environ('EC2_PRIVATE_KEY')
        if self.user is None:
            self.user = self.get_environ('EC2_USER_ID')
        if self.ec2cert_path is None:
            self.ec2cert_path = self.get_environ('EUCALYPTUS_CERT')
        self.inherit = not self.no_inherit
        excludes_string = self.exclude
        
        bundler = euca2ools.bundler.Bundler(self)
        
        self.user = self.user.replace('-', '')

        if self.generate_fstab and self.fstab_path:
            msg = '--generate-fstab and --fstab path cannot both be set.'
            self.display_error_and_exit(msg)
        if not self.fstab_path:
            if platform.machine() == 'i386':
                self.fstab_path = 'old'
            else:
                self.fstab_path = 'new'
        self.check_root()
        if self.size > MAX_IMAGE_SIZE:
            msg = 'Image Size is too large (Max = %d MB)' % MAX_IMAGE_SIZE
            self.display_error_and_exit(msg)
        self.volume_path = os.path.normpath(self.volume_path)

        noex='EUCA_BUNDLE_VOL_EMPTY_EXCLUDES'
        if noex in os.environ and os.environ[noex] != "0":
            excludes = []
        else:
            excludes = ['/etc/udev/rules.d/70-persistent-net.rules',
                        '/etc/udev/rules.d/z25_persistent-net.rules']

        if not self.all:
            excludes.extend(self.parse_excludes(excludes_string))
            bundler.add_excludes(self.volume_path, excludes)
        if self.inherit:
            (self.ramdisk_id, self.kernel_id, self.block_device_mapping, self.product_codes,
             ancestor_ami_ids) = self.get_instance_metadata(self.ramdisk_id,
                                                            self.kernel_id,
                                                            self.block_device_mapping)
        if self.product_codes:
            self.product_codes = self.add_product_codes(self.product_codes)

        try:
            fsinfo = bundler.get_fs_info(self.volume_path)
        except UnsupportedException, e:
            print e
            sys.exit(1)
        try:
            image_path = bundler.make_image(self.size, excludes, self.prefix,
                                            self.destination_path,
                                            fs_type=fsinfo['fs_type'],
                                            uuid=fsinfo['uuid'],
                                            label=fsinfo['label'])

        except NotFoundError:
            sys.exit(1)
        except UnsupportedException:
            sys.exit(1)
        image_path = os.path.normpath(image_path)
        if image_path.find(self.volume_path) == 0:
            exclude_image = image_path.replace(self.volume_path, '', 1)
            image_path_parts = exclude_image.split('/')
            if len(image_path_parts) > 1:
                exclude_image = \
                    exclude_image.replace(image_path_parts[0] + '/', ''
                        , 1)
            excludes.append(exclude_image)
        try:
            bundler.copy_volume(image_path, self.volume_path, excludes,
                                self.generate_fstab, self.fstab_path)
        except CopyError:
            print 'Unable to copy files'
            self.cleanup(image_path)
            sys.exit(1)
        except (NotFoundError, CommandFailed, UnsupportedException):
            self.cleanup(image_path)
            sys.exit(1)

        image_size = bundler.check_image(image_path, self.destination_path)
        if not self.prefix:
            self.prefix = self.get_relative_filename(image_path)
        try:
            (tgz_file, sha_tar_digest) = bundler.tarzip_image(self.prefix,
                                                              image_path,
                                                              self.destination_path)
        except (NotFoundError, CommandFailed):
            sys.exit(1)

        (encrypted_file, key, iv, bundled_size) = \
            bundler.encrypt_image(tgz_file)
        os.remove(tgz_file)
        (parts, parts_digest) = bundler.split_image(encrypted_file)
        bundler.generate_manifest(self.destination_path, self.prefix,
                                  parts, parts_digest, image_path,
                                  key, iv, self.cert_path, self.ec2cert_path,
                                  self.private_key_path, self.target_architecture,
                                  image_size, bundled_size,
                                  sha_tar_digest, self.user, self.kernel_id,
                                  self.ramdisk_id, self.block_device_mapping,
                                  self.product_codes, ancestor_ami_ids)
        os.remove(encrypted_file)

    def main_cli(self):
        self.main()
