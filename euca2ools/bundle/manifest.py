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

import lxml.objectify

import euca2ools.bundle.blockdevicemapping
import euca2ools.bundle.part


class BundleManifest(object):
    def __init__(self):
        self.image_arch = None
        self.kernel_id = None
        self.ramdisk_id = None
        self.block_device_mappings = []
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
        self.parts = []

    @classmethod
    def read_from_file(cls, manifest_filename, privkey_filename):
        with open(manifest_filename) as manifest_file:
            xml = lxml.objectify.parse(manifest_file).getroot()
        manifest = cls()
        mconfig = xml.machine_configuration
        manifest.image_arch = mconfig.arch.text
        if hasattr(mconfig, 'kernel_id'):
            manifest.kernel_id = mconfig.kernel_id.text
        if hasattr(mconfig, 'ramdisk_id'):
            manifest.ramdisk_id = mconfig.ramdisk_id.text
        if hasattr(mconfig, 'block_device_mappings'):
            for xml_mapping in mconfig.block_device_mappings.iter(
                    tag='block_device_mapping'):
                manifest.block_device_mappings.append(
                    euca2ools.bundle.blockdevicemapping.BlockDeviceMapping(
                        device=xml_mapping.device.text,
                        virtual=xml_mapping.virtual.text)
        if hasattr(mconfig, 'productcodes'):
            for xml_pcode in mconfig.productcodes.iter(tag='product_code'):
                manifest.product_codes.append(xml_pcode.text)
        manifest.image_name = xml.image.name.text
        manifest.account_id = xml.image.user.text
        manifest.image_digest = xml.image.digest.text
        manifest.image_digest_algorithm = xml.image.digest.get('algorithm')
        manifest.image_size = int(xml.image.size.text)
        manifest.bundled_image_size = int(xml.image.bundled_size.text)
        try:
            manifest.enc_key = _decrypt_hex(xml.image.user_encrypted_key.text,
                                            privkey_filename)
        except ValueError:
            manifest.enc_key = _decrypt_hex(xml.image.ec2_encrypted_key.text,
                                            privkey_filename)
        manifest.enc_algorithm = xml.image.user_encrypted_key.get('algorithm')
        try:
            manifest.enc_iv = _decrypt_hex(xml.image.user_encrypted_iv.text,
                                           privkey_filename)
        except ValueError:
            manifest.enc_iv = _decrypt_hex(xml.image.ec2_encrypted_iv.text,
                                           privkey_filename)
        manifest.parts = [None] * int(xml.parts.get('count'))
        for xml_part in xml.parts.iter(tag='part'):
            index = int(xml_part.get('index'))
            manifest.parts[index] = euca2ools.bundle.part.BundlePart(
                xml_part.filename.text, xml_part.digest.text,
                xml_part.digest.get('algorithm'))
        return manifest


def _decrypt_hex(hex_encrypted_key, privkey_filename):
    popen = subprocess.Popen(['openssl', 'rsautl', '-decrypt', '-pkcs',
                              '-inkey', privkey_filename],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (decrypted_key, __) = popen.communicate(binascii.unhexlify(key))
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
