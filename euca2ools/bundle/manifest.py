# Copyright 2013 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import binascii
import hashlib
import logging
import os.path
import subprocess

import lxml.etree
import lxml.objectify

import euca2ools.bundle


class BundleManifest(object):
    def __init__(self, loglevel=None):
        self.log = logging.getLogger(self.__class__.__name__)
        if loglevel is not None:
            self.log.level = loglevel
        self.image_arch = None
        self.kernel_id = None
        self.ramdisk_id = None
        self.block_device_mappings = {}  # virtual -> device
        self.product_codes = []
        self.image_name = None
        self.account_id = None
        self.image_type = None
        self.image_digest = None
        self.image_digest_algorithm = None
        self.image_size = None
        self.bundled_image_size = None
        self.enc_key = None
        self.enc_iv = None
        self.enc_algorithm = None
        self.image_parts = []

    @classmethod
    def read_from_file(cls, manifest_filename, privkey_filename):
        with open(manifest_filename) as manifest_file:
            xml = lxml.objectify.parse(manifest_file).getroot()
        manifest = cls()
        mconfig = xml.machine_configuration
        manifest.image_arch = mconfig.architecture.text.strip()
        if hasattr(mconfig, 'kernel_id'):
            manifest.kernel_id = mconfig.kernel_id.text.strip()
        if hasattr(mconfig, 'ramdisk_id'):
            manifest.ramdisk_id = mconfig.ramdisk_id.text.strip()
        if hasattr(mconfig, 'block_device_mappings'):
            for xml_mapping in mconfig.block_device_mappings.iter(
                    tag='block_device_mapping'):
                device = xml_mapping.device.text.strip()
                virtual = xml_mapping.virtual.text.strip()
                manifest.block_device_mappings[virtual] = device
        if hasattr(mconfig, 'productcodes'):
            for xml_pcode in mconfig.productcodes.iter(tag='product_code'):
                manifest.product_codes.append(xml_pcode.text.strip())
        manifest.image_name = xml.image.name.text.strip()
        manifest.account_id = xml.image.user.text.strip()
        manifest.image_type = xml.image.type.text.strip()
        manifest.image_digest = xml.image.digest.text.strip()
        manifest.image_digest_algorithm = xml.image.digest.get('algorithm')
        manifest.image_size = int(xml.image.size.text.strip())
        manifest.bundled_image_size = int(xml.image.bundled_size.text.strip())
        ## TODO:  test this
        try:
            manifest.enc_key = _decrypt_hex(
                xml.image.user_encrypted_key.text.strip(), privkey_filename)
        except ValueError:
            manifest.enc_key = _decrypt_hex(
                xml.image.ec2_encrypted_key.text.strip(), privkey_filename)
        manifest.enc_algorithm = xml.image.user_encrypted_key.get('algorithm')
        try:
            manifest.enc_iv = _decrypt_hex(
                xml.image.user_encrypted_iv.text.strip(), privkey_filename)
        except ValueError:
            manifest.enc_iv = _decrypt_hex(
                xml.image.ec2_encrypted_iv.text.strip(), privkey_filename)

        manifest.image_parts = [None] * int(xml.image.parts.get('count'))
        for xml_part in xml.image.parts.iter(tag='part'):
            index = int(xml_part.get('index'))
            manifest.image_parts[index] = euca2ools.bundle.BundlePart(
                xml_part.filename.text.strip(), xml_part.digest.text.strip(),
                xml_part.digest.get('algorithm'))
        for index, part in enumerate(manifest.image_parts):
            if part is None:
                raise ValueError('part {0} must not be None'.format(index))
        return manifest

    def dump_to_str(self, privkey_filename, user_cert_filename,
                    ec2_cert_filename, pretty_print=False):
        ec2_fp = euca2ools.bundle.util.get_cert_fingerprint(ec2_cert_filename)
        user_fp = euca2ools.bundle.util.get_cert_fingerprint(user_cert_filename)
        self.log.info('creating manifest for EC2 service with fingerprint %s',
                      ec2_fp)
        self.log.debug('EC2 certificate:  %s', ec2_cert_filename)
        self.log.debug('user certificate: %s', user_cert_filename)
        self.log.debug('user private key: %s', privkey_filename)

        xml = lxml.objectify.Element('manifest')

        # Manifest version
        xml.version = '2007-10-10'

        # Our version
        xml.bundler = None
        xml.bundler.name = 'euca2ools'
        xml.bundler.version = euca2ools.__version__
        xml.bundler.release = 0

        # Target hardware
        xml.machine_configuration = None
        mconfig = xml.machine_configuration
        assert self.image_arch is not None
        mconfig.architecture = self.image_arch
        # kernel_id and ramdisk_id are normally meaningful only for machine
        # images, but eucalyptus also uses them to indicate kernel and ramdisk
        # images using the magic string "true", so their presence cannot be
        # made contingent on whether the image is a machine image or not.  Be
        # careful not to create invalid kernel or ramdisk manifests because of
        # this.
        if self.kernel_id:
            mconfig.kernel_id = self.kernel_id
        if self.ramdisk_id:
            mconfig.ramdisk_id = self.ramdisk_id
        if self.image_type == 'machine':
            if self.block_device_mappings:
                mconfig.block_device_mapping = None
                for virtual, device in sorted(
                        self.block_device_mappings.items()):
                    xml_mapping = lxml.objectify.Element('mapping')
                    xml_mapping.device = device
                    xml_mapping.virtual = virtual
                    mconfig.block_device_mapping.append(xml_mapping)
            if self.product_codes:
                mconfig.product_codes = None
                for code in self.product_codes:
                    xml_code = lxml.objectify.Element('product_code')
                    mconfig.product_codes.append(xml_code)
                    mconfig.product_codes.product_code[-1] = code

        # Image info
        xml.image = None
        assert self.image_name is not None
        xml.image.name = self.image_name
        assert self.account_id is not None
        xml.image.user = self.account_id
        assert self.image_digest is not None
        xml.image.digest = self.image_digest
        assert self.image_digest_algorithm is not None
        xml.image.digest.set('algorithm', self.image_digest_algorithm)

        assert self.image_size is not None
        xml.image.size = self.image_size
        assert self.bundled_image_size is not None
        xml.image.bundled_size = self.bundled_image_size
        assert self.image_type is not None

        xml.image.type = self.image_type

        # Bundle encryption keys (these are cloud-specific)
        assert self.enc_key is not None
        assert self.enc_iv is not None
        assert self.enc_algorithm is not None
        #xml.image.append(lxml.etree.Comment(' EC2 cert fingerprint:  {0} '
        #                                    .format(ec2_fp)))
        xml.image.ec2_encrypted_key = _public_encrypt(self.enc_key,
                                                      ec2_cert_filename)
        xml.image.ec2_encrypted_key.set('algorithm', self.enc_algorithm)
        #xml.image.append(lxml.etree.Comment(' User cert fingerprint: {0} '
        #                                    .format(user_fp)))
        xml.image.user_encrypted_key = _public_encrypt(self.enc_key,
                                                       user_cert_filename)
        xml.image.user_encrypted_key.set('algorithm', self.enc_algorithm)
        xml.image.ec2_encrypted_iv = _public_encrypt(self.enc_iv,
                                                     ec2_cert_filename)
        xml.image.user_encrypted_iv = _public_encrypt(self.enc_iv,
                                                      user_cert_filename)

        # Bundle parts
        xml.image.parts = None
        xml.image.parts.set('count', str(len(self.image_parts)))
        for index, part in enumerate(self.image_parts):
            if part is None:
                raise ValueError('part {0} must not be None'.format(index))
            part_elem = lxml.objectify.Element('part')
            part_elem.set('index', str(index))
            part_elem.filename = os.path.basename(part.filename)
            part_elem.digest = part.hexdigest
            part_elem.digest.set('algorithm', part.digest_algorithm)
            #part_elem.append(lxml.etree.Comment(
            #    ' size: {0} '.format(part.size)))
            xml.image.parts.append(part_elem)

        # Cleanup for signature
        lxml.objectify.deannotate(xml, xsi_nil=True)
        lxml.etree.cleanup_namespaces(xml)
        to_sign = (lxml.etree.tostring(xml.machine_configuration) +
                   lxml.etree.tostring(xml.image))
        self.log.debug('string to sign: %s', repr(to_sign))
        signature = _rsa_sha1_sign(to_sign, privkey_filename)
        xml.signature = signature
        self.log.debug('hex-encoded signature: %s', signature)
        lxml.objectify.deannotate(xml, xsi_nil=True)
        lxml.etree.cleanup_namespaces(xml)
        self.log.debug('-- manifest content --\n', extra={'append': True})
        pretty_manifest = lxml.etree.tostring(xml, pretty_print=True).strip()
        self.log.debug('%s', pretty_manifest, extra={'append': True})
        self.log.debug('-- end of manifest content --')
        return lxml.etree.tostring(xml, pretty_print=pretty_print).strip()

    def dump_to_file(self, manifest_file, privkey_filename,
                     user_cert_filename, ec2_cert_filename):
        manifest_file.write(self.dump_to_str(
            privkey_filename, user_cert_filename, ec2_cert_filename))

    #@property
    #def bundled_image_size(self):
    #    return sum(part.size for part in self.image_parts)


def _decrypt_hex(hex_encrypted_key, privkey_filename):
    popen = subprocess.Popen(['openssl', 'rsautl', '-decrypt', '-pkcs',
                              '-inkey', privkey_filename],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    binary_encrypted_key = binascii.unhexlify(hex_encrypted_key)
    (decrypted_key, _) = popen.communicate(binary_encrypted_key)
    try:
        # Make sure it might actually be an encryption key.
        # This isn't perfect, but it's still better than nothing.
        int(decrypted_key, 16)
        return decrypted_key
    except ValueError:
        pass
    raise ValueError("Failed to decrypt the bundle's encryption key.  "
                     "Ensure the key supplied matches the one used for "
                     "bundling.")


def _public_encrypt(content, cert_filename):
    popen = subprocess.Popen(['openssl', 'rsautl', '-encrypt', '-pkcs',
                              '-inkey', cert_filename, '-certin'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, _) = popen.communicate(content)
    return binascii.hexlify(stdout)


def _rsa_sha1_sign(content, privkey_filename):
    digest = hashlib.sha1()
    digest.update(content)
    popen = subprocess.Popen(['openssl', 'pkeyutl', '-sign', '-inkey',
                              privkey_filename, '-pkeyopt', 'digest:sha1'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, _) = popen.communicate(digest.digest())
    return binascii.hexlify(stdout)
