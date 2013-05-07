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
from euca2ools.commands import Euca2ools
from euca2ools.commands.argtypes import delimited_list, filesize
from euca2ools.commands.bundle import add_bundle_creds
from euca2ools.commands.bundle.bundle import Bundle
import hashlib
import lxml.etree
import lxml.objectify
import os.path
from requestbuilder import Arg
from requestbuilder.command import BaseCommand
from requestbuilder.exceptions import ArgumentError
from requestbuilder.mixins import FileTransferProgressBarMixin
from requestbuilder.util import set_userregion
import subprocess
import tempfile


def manifest_block_device_mappings(mappings_as_str):
    mappings = {}
    mapping_strs = mappings_as_str.split(',')
    for mapping_str in mapping_strs:
        if mapping_str.strip():
            bits = mapping_str.strip().split('=')
            if len(bits) == 2:
                mappings[bits[0].strip()] = bits[1].strip()
            else:
                raise argparse.ArgumentTypeError(
                    "invalid device mapping '{0}' (must have format "
                    "'VIRTUAL=DEVICE')".format(mapping_str))
    return mappings


class BundleImage(BaseCommand, FileTransferProgressBarMixin):
    DESCRIPTION = 'Prepare an image for uploading to a cloud'
    SUITE = Euca2ools
    ARGS = [Arg('-i', '--image', metavar='FILE', required=True,
                help='file containing the image to bundle (required)'),
            Arg('-r', '--arch', choices=('i386', 'x86_64', 'armhf'),
                required=True,
                help="the image's processor architecture (required)"),
            Arg('--region', dest='userregion', metavar='USER@REGION',
                help='''use encryption keys and the account ID specified for
                a user and/or region in configuration files'''),
            Arg('-c', '--cert', metavar='FILE',
                help='file containing your X.509 certificate.'),
            Arg('-k', '--privatekey', metavar='FILE', help='''file containing
                the private key to sign the bundle's manifest with.  This
                private key will also be required to unbundle the image in
                the future.'''),
            Arg('-u', '--user', metavar='ACCOUNT', help='your account ID'),
            Arg('-d', '--destination', metavar='DIR', help='''location to
                place the bundle's files (default:  dir named by TMPDIR, TEMP,
                or TMP environment variables, or otherwise /var/tmp)'''),
            Arg('-p', '--prefix', help='''the file name prefix to give the
                bundle's files (default: the image's file name)'''),
            Arg('--ec2cert', metavar='FILE', help='''file containing the
                cloud's X.509 certificate'''),
            Arg('--kernel', metavar='IMAGE', help='''[machine image only] ID
                of the kernel image to associate with the bundle'''),
            Arg('--ramdisk', metavar='IMAGE', help='''[machine image only] ID
                of the ramdisk image to associate with the bundle'''),
            Arg('--block-device-mappings',
                metavar='VIRTUAL1=DEVICE1,VIRTUAL2=DEVICE2,...',
                type=manifest_block_device_mappings,
                help='''[machine image only] default block device mapping
                scheme with which to launch instances of this image'''),
            Arg('--productcodes', metavar='CODE1,CODE2,...',
                type=delimited_list(','),
                help='comma-separated list of product codes'),
            Arg('--batch', action='store_true', help=argparse.SUPPRESS),
            Arg('--part-size', type=filesize, default=10485760,  # 10m
                help=argparse.SUPPRESS),
            Arg('--image-type', choices=('machine', 'kernel', 'ramdisk'),
                default='machine', help=argparse.SUPPRESS),
            Arg('--progressbar-label', help=argparse.SUPPRESS)]

    def configure(self):
        BaseCommand.configure(self)
        set_userregion(self.config, self.args.get('userregion'))
        set_userregion(self.config, os.getenv('EUCA_REGION'))

        # Get creds
        add_bundle_creds(self.args, self.config)
        if not self.args.get('cert'):
            raise ArgumentError(
                'missing certificate; please supply one with -c')
        self.log.debug('certificate: %s', self.args['cert'])
        if not self.args.get('privatekey'):
            raise ArgumentError(
                'missing private key; please supply one with -k')
        self.log.debug('private key: %s', self.args['privatekey'])
        if not self.args.get('ec2cert'):
            raise ArgumentError(
                'missing cloud certificate; please supply one with --ec2cert')
        self.log.debug('cloud certificate: %s', self.args['ec2cert'])
        if not self.args.get('user'):
            raise ArgumentError(
                'missing account ID; please supply one with --user')
        self.log.debug('account ID: %s', self.args['user'])

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
        if (self.args.get('destination') and
            os.path.exists(self.args['destination']) and not
            os.path.isdir(self.args['destination'])):
            raise ArgumentError("argument -d/--destination: '{0}' is not a "
                                "directory".format(self.args['destination']))

    def main(self):
        prefix = (self.args.get('prefix') or
                  os.path.basename(self.args['image']))
        if self.args.get('destination'):
            path_prefix = os.path.join(self.args['destination'], prefix)
            if not os.path.exists(self.args['destination']):
                os.mkdir(self.args['destination'])
        else:
            tempdir_base = (os.getenv('TMPDIR') or os.getenv('TEMP') or
                            os.getenv('TMP') or '/var/tmp')
            tempdir = tempfile.mkdtemp(prefix='bundle-', dir=tempdir_base)
            path_prefix = os.path.join(tempdir, prefix)
        self.log.debug('bundle path prefix: %s', path_prefix)

        label = self.args.get('progressbar_label', 'Bundling image')
        bar = self.get_progressbar(label=label,
                                   maxval=os.path.getsize(self.args['image']))
        bundle = Bundle.create_from_image(
            self.args['image'], path_prefix,
            part_size=self.args.get('part_size'), progressbar=bar)
        manifest = self.generate_manifest_xml(bundle)
        manifest_filename = path_prefix + '.manifest.xml'
        with open(manifest_filename, 'w') as manifest_file:
            manifest_file.write(manifest)
        return (part['path'] for part in bundle.parts), manifest_filename

    def print_result(self, result):
        for part_filename in result[0]:
            print 'Wrote', part_filename
        print 'Wrote manifest', result[1]  # manifest

    def process_userregion(self, userregion):
        if '@' in userregion:
            user, region = userregion.split('@', 1)
        else:
            user = None
            region = userregion
        if region and self.config.current_region is None:
            self.config.current_region = region
        if user and self.config.current_user is None:
            self.config.current_user = user

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
