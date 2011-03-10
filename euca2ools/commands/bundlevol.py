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
import platform
import eucacommand
from boto.roboto.param import Param
import euca2ools.bundler
import euca2ools.metadata
from euca2ools.exceptions import *

MAX_IMAGE_SIZE = 1024 * 10

class BundleVol(eucacommand.EucaCommand):

    Description = 'Bundles an image for use with Eucalyptus or Amazon EC2.'
    Options = [Param(name='size', short_name='s', long_name='size',
                     optional=False, ptype='file',
                     doc='Size of the image in MB (default 10240)'),
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
               Param(name='all', short_name='a', long_name='all',
                     optional=True, ptype='boolean',
                     doc="""Bundle all directories (including
                     mounted filesystems."""),
               Param(name='prefix', short_name='p', long_name='prefix',
                     optional=True, ptype='string',
                     doc="""The prefix for the bundle image files.
                     (default: image name)."""),
               Param(name='no_inherit',  long_name='no-inherit',
                     optional=True, ptype='boolean',
                     doc='Do not add instance metadata to the bundled image.'),
               Param(name='exclude',  short_name='e', long_name='exclude',
                     optional=True, ptype='string',
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
               Param(name='destination',
                     short_name='d', long_name='destination',
                     optional=True, ptype='string',
                     doc="""Directory to store the bundled image in.
                     Defaults to /tmp.  Recommended."""),
               Param(name='ec2cert_path', long_name='ec2cert',
                     optional=True, ptype='file',
                     doc="Path to the Cloud's X509 public key certificate."),
               Param(name='target_architecture',
                     short_name='r', long_name='arch',
                     optional=True, ptype='string',
                     doc="""Target architecture for the image
                     Valid values: i386 | x86_64."""),
               Param(name='volume', long_name='volume',
                     optional=True, ptype='file',
                     doc='Path to mounted volume to bundle.'),
               Param(name='fstab_path', long_name='fstab',
                     optional=True, ptype='file',
                     doc='Path to the fstab to be bundled with image.'),
               Param(name='generate_fstab', long_name='generate-fstab',
                     optional=True, ptype='boolean',
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

    def check_image_size(self, size_str):
        try:
            size_in_mb = int(size_str)
        except ValueError:
            msg = 'Size must be an integer value'
            self.display_error_and_exit(msg)
        if size_in_mb > MAX_IMAGE_SIZE:
            msg = 'Image Size is too large (Max = %d MB)' % MAX_IMAGE_SIZE
            self.display_error_and_exit(msg)
        return size_in_mb

    def parse_excludes(self, excludes_string):
        excludes = []
        if excludes_string:
            excludes_string = excludes_string.replace(' ', '')
            excludes = excludes_string.split(',')
        return excludes

    def get_instance_metadata(self, ramdisk, kernel, mapping):
        md = euca2ools.metadata.MetaData()
        product_codes = None
        ramdisk_id = ramdisk
        kernel_id = kernel
        block_dev_mapping = mapping
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

    def cleanup(path):
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
        size = self.options.get('size', '%d' % MAX_IMAGE_SIZE)
        volume_path = self.options.get('volume_path', '/')
        cert_path = self.options.get('cert_path',
                                     self.get_environ('EC2_CERT'))
        private_key_path = self.options.get('private_key_path',
                                            self.get_environ('EC2_PRIVATE_KEY'))
        user = self.options.get('user', self.get_environ('EC2_USER_ID'))
        ec2cert_path = self.options.get('ec2cert_path',
                                        self.get_environ('EUCALYPTUS_CERT'))
        kernel = self.options.get('kernel_id', None)
        ramdisk = self.options.get('ramdisk_id', None)
        prefix = self.options.get('prefix', 'prefix')
        destination_path = self.options.get('destination_path', '/disk1')
        target_arch = self.options.get('target_arch', 'x86_64')
        block_device_map = self.options.get('block_device_map', None)
        product_codes = self.options.get('product_codes', None)
        inherit = not self.options.get('no_inherit', False)
        generate_fstab = self.options.get('generate_fstab', False)
        fstab_path = self.options.get('fstab_path', None)
        
        bundler = euca2ools.bundler.Bundler(self)
        
        user = user.replace('-', '')

        # TODO: these should be handled automatically with ftype="file"
        self.validate_dir(volume_path)
        self.validate_file(cert_path)
        self.validate_file(private_key_path)
        self.validate_file(ec2cert_path)

        if generate_fstab and fstab_path:
            msg = '--generate-fstab and --fstab path cannot both be set.'
            self.display_error_and_exit(msg)
        if fstab_path:
            self.validate_file(fstab_path)
        if not fstab_path:
            if platform.machine() == 'i386':
                fstab_path = 'old'
            else:
                fstab_path = 'new'
        self.check_root()
        size_in_mb = self.check_image_size(size)
        volume_path = os.path.normpath(volume_path)

        noex='EUCA_BUNDLE_VOL_EMPTY_EXCLUDES'
        if noex in os.environ and os.environ[noex] != "0":
            excludes = []
        else:
            excludes = ['/etc/udev/rules.d/70-persistent-net.rules',
                        '/etc/udev/rules.d/z25_persistent-net.rules']

        if not all:
            excludes.extend(self.parse_excludes(excludes_string))
            self.add_excludes(volume_path, excludes)
        if inherit:
            (ramdisk, kernel, block_device_map, product_codes,
             ancestor_ami_ids) = self.get_instance_metadata(ramdisk,
                                                            kernel,
                                                            block_device_map)
        if product_codes:
            product_codes = self.add_product_codes(product_codes)

        try:
            fsinfo = bundler.get_fs_info(volume_path)
        except UnsupportedException, e:
            print e
            sys.exit(1)
        try:
            image_path = bundler.make_image(size_in_MB, excludes, prefix,
                                            destination_path,
                                            fs_type=fsinfo['fs_type'],
                                            uuid=fsinfo['uuid'],
                                            label=fsinfo['label'])

        except NotFoundError:
            sys.exit(1)
        except UnsupportedException:
            sys.exit(1)
        image_path = os.path.normpath(image_path)
        if image_path.find(volume_path) == 0:
            exclude_image = image_path.replace(volume_path, '', 1)
            image_path_parts = exclude_image.split('/')
            if len(image_path_parts) > 1:
                exclude_image = \
                    exclude_image.replace(image_path_parts[0] + '/', ''
                        , 1)
            excludes.append(exclude_image)
        try:
            bundler.copy_volume(image_path, volume_path, excludes,
                                generate_fstab, fstab_path)
        except CopyError:
            print 'Unable to copy files'
            self.cleanup(image_path)
            sys.exit(1)
        except (NotFoundError, CommandFailed, UnsupportedException):
            self.cleanup(image_path)
            sys.exit(1)

        image_size = bundler.check_image(image_path, destination_path)
        if not prefix:
            prefix = self.get_relative_filename(image_path)
        try:
            (tgz_file, sha_tar_digest) = bundler.tarzip_image(prefix, image_path,
                                                              destination_path)
        except (NotFoundError, CommandFailed):
            sys.exit(1)

        (encrypted_file, key, iv, bundled_size) = \
            bundler.encrypt_image(tgz_file)
        os.remove(tgz_file)
        (parts, parts_digest) = bundler.split_image(encrypted_file)
        bundler.generate_manifest(destination_path, prefix,
                                  parts, parts_digest, image_path,
                                  key, iv, cert_path, ec2cert_path,
                                  private_key_path, target_arch,
                                  image_size, bundled_size,
                                  sha_tar_digest, user, kernel,
                                  ramdisk, block_device_map, product_codes,
                                  ancestor_ami_ids)
        os.remove(encrypted_file)
