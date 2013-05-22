# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Eucalyptus Systems, Inc.
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

import argparse
import binascii
import euca2ools
from euca2ools.commands.bundle import BundleCreator
from euca2ools.commands.bundle.bundle import Bundle
from euca2ools.util import mkdtemp_for_large_files
import hashlib
import lxml.etree
import lxml.objectify
import os.path
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError
import subprocess


class BundleImage(BundleCreator):
    DESCRIPTION = 'Prepare an image for uploading to a cloud'
    ARGS = [Arg('-i', '--image', metavar='FILE', required=True,
                help='file containing the image to bundle (required)'),
            Arg('-p', '--prefix', help='''the file name prefix to give the
                bundle's files (default: the image's file name)'''),
            Arg('--image-type', choices=('machine', 'kernel', 'ramdisk'),
                default='machine', help=argparse.SUPPRESS),
            Arg('--progressbar-label', help=argparse.SUPPRESS)]

    def configure(self):
        BundleCreator.configure(self)

        # kernel/ramdisk image IDs
        if self.args.get('kernel') == 'true':
            self.args['image_type'] = 'kernel'
        if self.args.get('ramdisk') == 'true':
            self.args['image_type'] = 'ramdisk'
        if self.args['image_type'] == 'kernel':
            if self.args.get('kernel') and self.args['kernel'] != 'true':
                raise ArgumentError("argument --kernel: not compatible with "
                                    "image type 'kernel'")
            if self.args.get('ramdisk'):
                raise ArgumentError("argument --ramdisk: not compatible with "
                                    "image type 'kernel'")
        if self.args['image_type'] == 'ramdisk':
            if self.args.get('kernel'):
                raise ArgumentError("argument --kernel: not compatible with "
                                    "image type 'ramdisk'")
            if self.args.get('ramdisk') and self.args['ramdisk'] != 'true':
                raise ArgumentError("argument --ramdisk: not compatible with "
                                    "image type 'ramdisk'")

    def main(self):
        prefix = (self.args.get('prefix') or
                  os.path.basename(self.args['image']))
        if self.args.get('destination'):
            path_prefix = os.path.join(self.args['destination'], prefix)
            if not os.path.exists(self.args['destination']):
                os.mkdir(self.args['destination'])
        else:
            tempdir = mkdtemp_for_large_files(prefix='bundle-')
            path_prefix = os.path.join(tempdir, prefix)
        self.log.debug('bundle path prefix: %s', path_prefix)

        label = self.args.get('progressbar_label', 'Bundling image')
        pbar = self.get_progressbar(label=label,
                                    maxval=os.path.getsize(self.args['image']))
        bundle = Bundle.create_from_image(
            self.args['image'], path_prefix,
            part_size=self.args.get('part_size'), progressbar=pbar)
        manifest = self.generate_manifest_xml(bundle)
        manifest_filename = path_prefix + '.manifest.xml'
        with open(manifest_filename, 'w') as manifest_file:
            manifest_file.write(manifest)
        return (part['path'] for part in bundle.parts), manifest_filename

    def print_result(self, result):
        for part_filename in result[0]:
            print 'Wrote', part_filename
        print 'Wrote manifest', result[1]  # manifest

    def generate_manifest_xml(self, bundle):
        manifest = lxml.objectify.Element('manifest')

        # Manifest version
        manifest.version = '2007-10-10'

        # Our version
        manifest.bundler = None
        manifest.bundler.name = 'euca2ools'
        manifest.bundler.version = euca2ools.__version__
        manifest.bundler.release = None

        # Target hardware
        manifest.machine_configuration = None
        manifest.machine_configuration.architecture = self.args['arch']
        if self.args.get('kernel'):
            manifest.machine_configuration.kernel_id = self.args['kernel']
        if self.args.get('ramdisk'):
            manifest.machine_configuration.ramdisk_id = self.args['ramdisk']
        if self.args['image_type'] == 'machine':
            bd_mappings = self.args.get('block_device_mappings', {})
            if bd_mappings:
                manifest.machine_configuration.block_device_mapping = None
                for virtual, device in sorted(bd_mappings.iteritems()):
                    bd_elem = lxml.objectify.Element('mapping')
                    bd_elem.virtual = virtual
                    bd_elem.device = device
                    manifest.machine_configuration.block_device_mapping.append(
                        bd_elem)
            if self.args.get('productcodes'):
                manifest.machine_configuration.product_codes = None
                for code in self.args['productcodes']:
                    code_elem = lxml.objectify.Element('product_code')
                    manifest.machine_configuration.product_codes.append(
                        code_elem)
                    (manifest.machine_configuration.product_codes
                     .product_code[-1]) = code

        # Image info
        manifest.image = None
        manifest.image.name = os.path.basename(bundle.image_filename)
        manifest.image.user = self.args['user']  # user's account ID
        manifest.image.type = self.args['image_type']  # machine/kernel/ramdisk
        if self.args['image_type'] == 'kernel':
            # This might need something else
            manifest.image.kernel_name = os.path.basename(
                bundle.image_filename)
        manifest.image.digest = bundle.digest
        manifest.image.digest.set('algorithm', bundle.digest_algorithm)
        manifest.image.size = bundle.image_size
        manifest.image.bundled_size = bundle.bundled_size

        # Bundle encryption keys (these are cloud-specific)
        manifest.image.ec2_encrypted_key = public_encrypt(bundle.enc_key,
                                                          self.args['ec2cert'])
        manifest.image.ec2_encrypted_key.set('algorithm', bundle.enc_algorithm)
        manifest.image.user_encrypted_key = public_encrypt(bundle.enc_key,
                                                           self.args['cert'])
        manifest.image.user_encrypted_key.set('algorithm',
                                              bundle.enc_algorithm)
        manifest.image.ec2_encrypted_iv = public_encrypt(bundle.enc_iv,
                                                         self.args['ec2cert'])
        manifest.image.user_encrypted_iv = public_encrypt(bundle.enc_iv,
                                                          self.args['cert'])

        # Bundle parts
        manifest.image.parts = None
        manifest.image.parts.set('count', str(len(bundle.parts)))
        for index, part in enumerate(bundle.parts):
            part_elem = lxml.objectify.Element('part')
            part_elem.set('index', str(index))
            part_elem.filename = os.path.basename(part['path'])
            part_elem.digest = part['digest']
            part_elem.digest.set('algorithm', bundle.digest_algorithm)
            manifest.image.parts.append(part_elem)

        # Parent image IDs
        if (self.args['image_type'] == 'machine' and
            self.args.get('ancestor_image_ids')):
            # I think this info only comes from the metadata service when you
            # run ec2-bundle-vol on an instance.  ec2-bundle-image doesn't seem
            # to have an option for it.
            manifest.image.ancestry = None
            for ancestor_image_id in self.args['ancestor_image_ids']:
                ancestor_elem = lxml.objectify.Element('ancestor_ami_id')
                manifest.image.ancestry.append(ancestor_elem)
                manifest.image.ancestry.ancestor_ami_id[-1] = ancestor_image_id

        lxml.objectify.deannotate(manifest, xsi_nil=True)
        lxml.etree.cleanup_namespaces(manifest)
        to_sign = (lxml.etree.tostring(manifest.machine_configuration) +
                   lxml.etree.tostring(manifest.image))
        self.log.debug('string to sign: %s', repr(to_sign))
        signature = rsa_sha1_sign(to_sign, self.args['privatekey'])
        manifest.signature = signature
        self.log.debug('hex-encoded signature: %s', signature)
        lxml.objectify.deannotate(manifest, xsi_nil=True)
        lxml.etree.cleanup_namespaces(manifest)
        self.log.debug('-- manifest content --\n', extra={'append': True})
        pretty_manifest = lxml.etree.tostring(manifest,
                                              pretty_print=True).strip()
        self.log.debug(pretty_manifest, extra={'append': True})
        self.log.debug('-- end of manifest content --')
        return lxml.etree.tostring(manifest)


def public_encrypt(content, cert_filename):
    popen = subprocess.Popen(['openssl', 'rsautl', '-encrypt', '-pkcs',
                              '-inkey', cert_filename, '-certin'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, __) = popen.communicate(content)
    return binascii.hexlify(stdout)


def rsa_sha1_sign(content, privkey_filename):
    digest = hashlib.sha1()
    digest.update(content)
    popen = subprocess.Popen(['openssl', 'pkeyutl', '-sign', '-inkey',
                              privkey_filename, '-pkeyopt', 'digest:sha1'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, __) = popen.communicate(digest.digest())
    return binascii.hexlify(stdout)
