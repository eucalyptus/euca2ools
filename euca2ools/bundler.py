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
import tarfile
from xml.dom.minidom import Document
from xml.dom import minidom
from hashlib import sha1 as sha
from M2Crypto import BN, EVP, RSA, X509
from binascii import hexlify, unhexlify
import subprocess
import tempfile
import stat
import platform
import re
import shutil
import logging
import base64
import image
import utils
from exceptions import *

BUNDLER_NAME = 'euca-tools'
BUNDLER_VERSION = '1.3.2'
VERSION = '2007-10-10'
RELEASE = '31337'
AES = 'AES-128-CBC'

IMAGE_IO_CHUNK = 10 * 1024
IMAGE_SPLIT_CHUNK = IMAGE_IO_CHUNK * 1024
MAX_LOOP_DEVS = 256

class Bundler(object):

    def __init__(self, euca):
        self.euca = euca
        system_string = platform.system()
        if system_string == 'Linux':
            self.img = image.LinuxImage(self.euca.debug)
        elif system_string == 'SunOS':
            self.img = image.SolarisImage(self.euca.debug)
        else:
            self.img = 'Unsupported'

    def split_file(self, file, chunk_size):
        parts = []
        parts_digest = []
        file_size = os.path.getsize(file)
        in_file = open(file, 'rb')
        number_parts = int(file_size / chunk_size)
        number_parts += 1
        bytes_read = 0
        for i in range(0, number_parts, 1):
            filename = '%s.%02d' % (file, i)
            part_digest = sha()
            file_part = open(filename, 'wb')
            print 'Part:', self.euca.get_relative_filename(filename)
            part_bytes_written = 0
            while part_bytes_written < IMAGE_SPLIT_CHUNK:
                data = in_file.read(IMAGE_IO_CHUNK)
                file_part.write(data)
                part_digest.update(data)
                data_len = len(data)
                part_bytes_written += data_len
                bytes_read += data_len
                if bytes_read >= file_size:
                    break
            file_part.close()
            parts.append(filename)
            parts_digest.append(hexlify(part_digest.digest()))

        in_file.close()
        return (parts, parts_digest)

    def check_image(self, image_file, path):
        print 'Checking image'
        if not os.path.exists(path):
            os.makedirs(path)
        image_size = os.path.getsize(image_file)
        if self.euca.debug:
            print 'Image Size:', image_size, 'bytes'
        return image_size

    def get_fs_info(self, path):
        fs_type = None
        uuid = None
        label = None
        devpth = None
        tmpd = None
        try:
            st_dev=os.stat(path).st_dev
            dev=os.makedev(os.major(st_dev),os.minor(st_dev))
            tmpd=tempfile.mkdtemp()
            devpth=("%s/dev" % tmpd)
            os.mknod(devpth,0400 | stat.S_IFBLK ,dev)
        except:
            raise

        ret = { }
        pairs = { 'LABEL' : 'label', 'UUID' : 'uuid' , 'FS_TYPE' : 'fs_type' }
        for (blkid_n, my_n) in pairs.iteritems():
            cmd = [ 'blkid', '-s%s' % blkid_n, '-ovalue', devpth ]
            print cmd
            try:
                output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
                ret[my_n]=output.rstrip()
            except Exception, e:
                os.unlink(devpth)
                os.rmdir(tmpd)
                raise UnsupportedException("Unable to determine %s for %s" % (blkid_n, path))

        os.unlink(devpth)
        os.rmdir(tmpd)
        return(ret)
   
    def tarzip_image(self, prefix, file, path):
        utils.check_prerequisite_command('tar')

        targz = '%s.tar.gz' % os.path.join(path, prefix)
        targzfile = open(targz, 'w')

        # make process pipes
        tar_cmd = ['tar', 'ch', '-S']
        file_path = self.euca.get_file_path(file)
        if file_path:
            tar_cmd.append('-C')
            tar_cmd.append(file_path)
            tar_cmd.append(self.euca.get_relative_filename(file))
        else:
            tar_cmd.append(file)
        tarproc = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)
        zipproc = subprocess.Popen(['gzip'], stdin=subprocess.PIPE, stdout=targzfile)

	# pass tar output to digest and gzip
        sha_image = sha()
        buf=os.read(tarproc.stdout.fileno(), 8196)
        while buf:
            zipproc.stdin.write(buf)
            sha_image.update(buf)
            buf=os.read(tarproc.stdout.fileno(), 8196)

        zipproc.stdin.close();
        targzfile.close()

        tarproc.wait()
        zipproc.wait()
        for p, pname in [(tarproc, 'tar'), (zipproc, 'gzip')]:
            if p.returncode != 0:
                print "'%s' returned error (%i)" % (pname, p.returncode)
                raise CommandFailed
            
        if os.path.getsize(targz) <= 0:
            print 'Could not tar/compress image'
            raise CommandFailed
        return (targz, hexlify(sha_image.digest()))

    def hexToBytes(self, hexString):
        bytes = []
        hexString = ''.join(hexString.split(' '))
        for i in range(0, len(hexString), 2):
            bytes.append(chr(int(hexString[i:i + 2], 16)))

        return ''.join(bytes)

    def crypt_file(self, cipher, in_file, out_file):
        while 1:
            buf = in_file.read(IMAGE_IO_CHUNK)
            if not buf:
                break
            out_file.write(cipher.update(buf))
        out_file.write(cipher.final())

    def encrypt_image(self, file):
        print 'Encrypting image'
        enc_file = '%s.part' % file.replace('.tar.gz', '')

        # get 17 bytes of randomness with top bit a '1'.
        # convert to a hex string like '0x<34 hex chars>L'
        # then take the last 32 of the hex digits, giving 32 random hex chars
        key = hex(BN.rand(17 * 8,top=0))[4:36]
        if self.euca.debug:
            print 'Key: %s' % key
        iv = hex(BN.rand(17 * 8,top=0))[4:36]
        if self.euca.debug:
            print 'IV: %s' % iv
             
        k = EVP.Cipher(alg='aes_128_cbc', key=unhexlify(key),
                       iv=unhexlify(iv), op=1)

        in_file = open(file, 'rb')
        out_file = open(enc_file, 'wb')
        self.crypt_file(k, in_file, out_file)
        in_file.close()
        out_file.close()
        bundled_size = os.path.getsize(enc_file)
        return (enc_file, key, iv, bundled_size)

    def split_image(self, file):
        print 'Splitting image...'
        return self.split_file(file, IMAGE_SPLIT_CHUNK)

    def get_verification_string(self, manifest_string):
        start_mc = manifest_string.find('<machine_configuration>')
        end_mc = manifest_string.find('</machine_configuration>')
        mc_config_string = manifest_string[start_mc:end_mc
            + len('</machine_configuration>')]
        start_image = manifest_string.find('<image>')
        end_image = manifest_string.find('</image>')
        image_string = manifest_string[start_image:end_image
            + len('</image>')]

        return mc_config_string + image_string

    def parse_manifest(self, manifest_filename):
        parts = []
        encrypted_key = None
        encrypted_iv = None
        dom = minidom.parse(manifest_filename)
        manifest_elem = dom.getElementsByTagName('manifest')[0]
        parts_list = manifest_elem.getElementsByTagName('filename')
        for part_elem in parts_list:
            nodes = part_elem.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    parts.append(node.data)
        encrypted_key_elem = \
            manifest_elem.getElementsByTagName('user_encrypted_key')[0]
        nodes = encrypted_key_elem.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                encrypted_key = node.data
        encrypted_iv_elem = \
            manifest_elem.getElementsByTagName('user_encrypted_iv')[0]
        nodes = encrypted_iv_elem.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                encrypted_iv = node.data
        return (parts, encrypted_key, encrypted_iv)

    def assemble_parts(self, src_directory, directory, manifest_path, parts):
        manifest_filename = self.euca.get_relative_filename(manifest_path)
        encrypted_filename = os.path.join(directory,
                manifest_filename.replace('.manifest.xml', '.enc.tar.gz'
                ))
        if len(parts) > 0:
            if not os.path.exists(directory):
                os.makedirs(directory)
            encrypted_file = open(encrypted_filename, 'wb')
            for part in parts:
                print 'Part:', self.euca.get_relative_filename(part)
                part_filename = os.path.join(src_directory, part)
                part_file = open(part_filename, 'rb')
                while 1:
                    data = part_file.read(IMAGE_IO_CHUNK)
                    if not data:
                        break
                    encrypted_file.write(data)
                part_file.close()
            encrypted_file.close()
        return encrypted_filename

    def decrypt_image(self, encrypted_filename, encrypted_key,
                      encrypted_iv, private_key_path):
        user_priv_key = RSA.load_key(private_key_path)
        key = user_priv_key.private_decrypt(unhexlify(encrypted_key),
                RSA.pkcs1_padding)
        iv = user_priv_key.private_decrypt(unhexlify(encrypted_iv),
                RSA.pkcs1_padding)
        k = EVP.Cipher(alg='aes_128_cbc', key=unhexlify(key),
                       iv=unhexlify(iv), op=0)

        decrypted_filename = encrypted_filename.replace('.enc', '')
        decrypted_file = open(decrypted_filename, 'wb')
        encrypted_file = open(encrypted_filename, 'rb')
        self.crypt_file(k, encrypted_file, decrypted_file)
        encrypted_file.close()
        decrypted_file.close()
        return decrypted_filename

    def decrypt_string(self, encrypted_string, private_key_path, encoded=False):
        user_priv_key = RSA.load_key(private_key_path)
        string_to_decrypt = encrypted_string
        if encoded:
            string_to_decrypt = base64.b64decode(encrypted_string)
        return user_priv_key.private_decrypt(string_to_decrypt,
                RSA.pkcs1_padding)

    def untarzip_image(self, path, file):
        untarred_filename = file.replace('.tar.gz', '')
        tar_file = tarfile.open(file, 'r|gz')
        tar_file.extractall(path)
        untarred_names = tar_file.getnames()
        tar_file.close()
        return untarred_names

    def get_block_devs(self, mapping):
        virtual = []
        devices = []

        vname = None
        for m in mapping:
            if not vname:
                vname = m
                virtual.append(vname)
            else:
                devices.append(m)
                vname = None

        return (virtual, devices)

    def generate_manifest(self, path, prefix, parts, parts_digest,
                          file, key, iv, cert_path, ec2cert_path,
                          private_key_path, target_arch,
                          image_size, bundled_size,
                          image_digest, user, kernel,
                          ramdisk, mapping=None,
                          product_codes=None, ancestor_ami_ids=None):
        user_pub_key = X509.load_cert(cert_path).get_pubkey().get_rsa()
        cloud_pub_key = \
            X509.load_cert(ec2cert_path).get_pubkey().get_rsa()

        user_encrypted_key = hexlify(user_pub_key.public_encrypt(key,
                RSA.pkcs1_padding))
        user_encrypted_iv = hexlify(user_pub_key.public_encrypt(iv,
                                    RSA.pkcs1_padding))

        cloud_encrypted_key = hexlify(cloud_pub_key.public_encrypt(key,
                RSA.pkcs1_padding))
        cloud_encrypted_iv = hexlify(cloud_pub_key.public_encrypt(iv,
                RSA.pkcs1_padding))

        user_priv_key = None
        if private_key_path:
            user_priv_key = RSA.load_key(private_key_path)

        manifest_file = '%s.manifest.xml' % os.path.join(path, prefix)
        if self.euca.debug:
            print 'Manifest: ', manifest_file

        print 'Generating manifest %s' % manifest_file

        manifest_out_file = open(manifest_file, 'wb')
        doc = Document()

        manifest_elem = doc.createElement('manifest')
        doc.appendChild(manifest_elem)

        # version

        version_elem = doc.createElement('version')
        version_value = doc.createTextNode(VERSION)
        version_elem.appendChild(version_value)
        manifest_elem.appendChild(version_elem)

        # bundler info

        bundler_elem = doc.createElement('bundler')
        bundler_name_elem = doc.createElement('name')
        bundler_name_value = doc.createTextNode(BUNDLER_NAME)
        bundler_name_elem.appendChild(bundler_name_value)
        bundler_version_elem = doc.createElement('version')
        bundler_version_value = doc.createTextNode(BUNDLER_VERSION)
        bundler_version_elem.appendChild(bundler_version_value)
        bundler_elem.appendChild(bundler_name_elem)
        bundler_elem.appendChild(bundler_version_elem)

           # release

        release_elem = doc.createElement('release')
        release_value = doc.createTextNode(RELEASE)
        release_elem.appendChild(release_value)
        bundler_elem.appendChild(release_elem)
        manifest_elem.appendChild(bundler_elem)

        # machine config

        machine_config_elem = doc.createElement('machine_configuration')
        manifest_elem.appendChild(machine_config_elem)

        target_arch_elem = doc.createElement('architecture')
        target_arch_value = doc.createTextNode(target_arch)
        target_arch_elem.appendChild(target_arch_value)
        machine_config_elem.appendChild(target_arch_elem)

        # block device mapping

        if mapping:
            block_dev_mapping_elem = \
                doc.createElement('block_device_mapping')
            (virtual_names, device_names) = self.get_block_devs(mapping)
            vname_index = 0
            for vname in virtual_names:
                dname = device_names[vname_index]
                mapping_elem = doc.createElement('mapping')
                virtual_elem = doc.createElement('virtual')
                virtual_value = doc.createTextNode(vname)
                virtual_elem.appendChild(virtual_value)
                mapping_elem.appendChild(virtual_elem)
                device_elem = doc.createElement('device')
                device_value = doc.createTextNode(dname)
                device_elem.appendChild(device_value)
                mapping_elem.appendChild(device_elem)
                block_dev_mapping_elem.appendChild(mapping_elem)
                vname_index = vname_index + 1
            machine_config_elem.appendChild(block_dev_mapping_elem)

        if product_codes:
            product_codes_elem = doc.createElement('product_codes')
            for product_code in product_codes:
                product_code_elem = doc.createElement('product_code')
                product_code_value = doc.createTextNode(product_code)
                product_code_elem.appendChild(product_code_value)
                product_codes_elem.appendChild(product_code_elem)
            machine_config_elem.appendChild(product_codes_elem)

        # kernel and ramdisk

        if kernel:
            kernel_id_elem = doc.createElement('kernel_id')
            kernel_id_value = doc.createTextNode(kernel)
            kernel_id_elem.appendChild(kernel_id_value)
            machine_config_elem.appendChild(kernel_id_elem)

        if ramdisk:
            ramdisk_id_elem = doc.createElement('ramdisk_id')
            ramdisk_id_value = doc.createTextNode(ramdisk)
            ramdisk_id_elem.appendChild(ramdisk_id_value)
            machine_config_elem.appendChild(ramdisk_id_elem)

        image_elem = doc.createElement('image')
        manifest_elem.appendChild(image_elem)

        # name

        image_name_elem = doc.createElement('name')
        image_name_value = \
            doc.createTextNode(self.euca.get_relative_filename(file))
        image_name_elem.appendChild(image_name_value)
        image_elem.appendChild(image_name_elem)

        # user

        user_elem = doc.createElement('user')
        user_value = doc.createTextNode('%s' % user)
        user_elem.appendChild(user_value)
        image_elem.appendChild(user_elem)

        # type
        # TODO: fixme

        image_type_elem = doc.createElement('type')
        image_type_value = doc.createTextNode('machine')
        image_type_elem.appendChild(image_type_value)
        image_elem.appendChild(image_type_elem)

    # ancestor ami ids

        if ancestor_ami_ids:
            ancestry_elem = doc.createElement('ancestry')
            for ancestor_ami_id in ancestor_ami_ids:
                ancestor_id_elem = doc.createElement('ancestor_ami_id')
                ancestor_id_value = doc.createTextNode(ancestor_ami_id)
                ancestor_id_elem.appendChild(ancestor_id_value)
                ancestry_elem.appendChild(ancestor_id_elem)
            image_elem.appendChild(ancestry_elem)

        # digest

        image_digest_elem = doc.createElement('digest')
        image_digest_elem.setAttribute('algorithm', 'SHA1')
        image_digest_value = doc.createTextNode('%s' % image_digest)
        image_digest_elem.appendChild(image_digest_value)
        image_elem.appendChild(image_digest_elem)

        # size

        image_size_elem = doc.createElement('size')
        image_size_value = doc.createTextNode('%s' % image_size)
        image_size_elem.appendChild(image_size_value)
        image_elem.appendChild(image_size_elem)

        # bundled size

        bundled_size_elem = doc.createElement('bundled_size')
        bundled_size_value = doc.createTextNode('%s' % bundled_size)
        bundled_size_elem.appendChild(bundled_size_value)
        image_elem.appendChild(bundled_size_elem)

        # key, iv

        cloud_encrypted_key_elem = doc.createElement('ec2_encrypted_key'
                )
        cloud_encrypted_key_value = doc.createTextNode('%s'
                % cloud_encrypted_key)
        cloud_encrypted_key_elem.appendChild(cloud_encrypted_key_value)
        cloud_encrypted_key_elem.setAttribute('algorithm', AES)
        image_elem.appendChild(cloud_encrypted_key_elem)

        user_encrypted_key_elem = doc.createElement('user_encrypted_key'
                )
        user_encrypted_key_value = doc.createTextNode('%s'
                % user_encrypted_key)
        user_encrypted_key_elem.appendChild(user_encrypted_key_value)
        user_encrypted_key_elem.setAttribute('algorithm', AES)
        image_elem.appendChild(user_encrypted_key_elem)

        cloud_encrypted_iv_elem = doc.createElement('ec2_encrypted_iv')
        cloud_encrypted_iv_value = doc.createTextNode('%s'
                % cloud_encrypted_iv)
        cloud_encrypted_iv_elem.appendChild(cloud_encrypted_iv_value)
        image_elem.appendChild(cloud_encrypted_iv_elem)

        user_encrypted_iv_elem = doc.createElement('user_encrypted_iv')
        user_encrypted_iv_value = doc.createTextNode('%s'
                % user_encrypted_iv)
        user_encrypted_iv_elem.appendChild(user_encrypted_iv_value)
        image_elem.appendChild(user_encrypted_iv_elem)

        # parts

        parts_elem = doc.createElement('parts')
        parts_elem.setAttribute('count', '%s' % len(parts))
        part_number = 0
        for part in parts:
            part_elem = doc.createElement('part')
            filename_elem = doc.createElement('filename')
            filename_value = \
                doc.createTextNode(self.euca.get_relative_filename(part))
            filename_elem.appendChild(filename_value)
            part_elem.appendChild(filename_elem)

            # digest

            part_digest_elem = doc.createElement('digest')
            part_digest_elem.setAttribute('algorithm', 'SHA1')
            part_digest_value = \
                doc.createTextNode(parts_digest[part_number])
            part_digest_elem.appendChild(part_digest_value)
            part_elem.appendChild(part_digest_elem)
            part_elem.setAttribute('index', '%s' % part_number)
            parts_elem.appendChild(part_elem)
            part_number += 1
        image_elem.appendChild(parts_elem)

        manifest_string = doc.toxml()

        if user_priv_key:
            string_to_sign = self.get_verification_string(manifest_string)
            signature_elem = doc.createElement('signature')
            sha_manifest = sha()
            sha_manifest.update(string_to_sign)
            signature_value = doc.createTextNode('%s'
                    % hexlify(user_priv_key.sign(sha_manifest.digest())))
            signature_elem.appendChild(signature_value)
            manifest_elem.appendChild(signature_elem)
            
        manifest_out_file.write(doc.toxml())
        manifest_out_file.close()
        return manifest_file

    def add_excludes(self, path, excludes):
        if self.euca.debug:
            print 'Reading /etc/mtab...'
        mtab_file = open('/etc/mtab', 'r')
        while 1:
            mtab_line = mtab_file.readline()
            if not mtab_line:
                break
            mtab_line_parts = mtab_line.split(' ')
            mount_point = mtab_line_parts[1]
            fs_type = mtab_line_parts[2]
            if mount_point.find(path) == 0 and fs_type \
                not in self.img.ALLOWED_FS_TYPES:
                if self.euca.debug:
                    print 'Excluding %s...' % mount_point
                excludes.append(mount_point)
        mtab_file.close()
        for banned in self.img.BANNED_MOUNTS:
            excludes.append(banned)

    def make_image(self, size_in_MB, excludes, prefix,
                   destination_path, fs_type = None,
                   uuid = None, label = None):
        image_file = '%s.img' % prefix
        image_path = '%s/%s' % (destination_path, image_file)
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        if self.img == 'Unsupported':
            print 'Platform not fully supported.'
            raise UnsupportedException
        self.img.create_image(size_in_MB, image_path)
        self.img.make_fs(image_path, fs_type=fs_type, uuid=uuid, label=label)
        return image_path

    def create_loopback(self, image_path):
        utils.check_prerequisite_command('losetup')
        tries = 0
        while tries < MAX_LOOP_DEVS:
            loop_dev = subprocess.Popen(['losetup', '-f'],
                                        stdout=subprocess.PIPE).communicate()[0].replace('\n', '')
            if loop_dev:
                output = subprocess.Popen(['losetup', '%s' % loop_dev, '%s'
                                           % image_path], stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
                if not output[1]:
                    return loop_dev
            else:
                print 'Could not create loopback device. Aborting'
                raise CommandFailed
            tries += 1

    def mount_image(self, image_path):
        utils.check_prerequisite_command('mount')

        tmp_mnt_point = '/tmp/%s' % hex(BN.rand(16))[2:6]
        if not os.path.exists(tmp_mnt_point):
            os.makedirs(tmp_mnt_point)
        if self.euca.debug:
            print 'Creating loopback device...'
        loop_dev = self.create_loopback(image_path)
        if self.euca.debug:
            print 'Mounting image...'
        subprocess.Popen(['mount', loop_dev, tmp_mnt_point],
              stdout=subprocess.PIPE).communicate()
        return (tmp_mnt_point, loop_dev)

    def copy_to_image(self, mount_point, volume_path, excludes):
        try:
            utils.check_prerequisite_command('rsync')
        except NotFoundError:
            raise CopyError
        rsync_cmd = ['rsync', '-aXS']
        for exclude in excludes:
            rsync_cmd.append('--exclude')
            rsync_cmd.append(exclude)
        rsync_cmd.append(volume_path)
        rsync_cmd.append(mount_point)
        if self.euca.debug:
            print 'Copying files...'
            for exclude in excludes:
                print 'Excluding:', exclude

        pipe = subprocess.Popen(rsync_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = pipe.communicate()
        for dir in self.img.ESSENTIAL_DIRS:
            dir_path = os.path.join(mount_point, dir)
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
                if dir == 'tmp':
                    os.chmod(dir_path, 01777)
        self.img.make_essential_devs(mount_point)
        mtab_file = open('/etc/mtab', 'r')
        while 1:
            mtab_line = mtab_file.readline()
            if not mtab_line:
                break
            mtab_line_parts = mtab_line.split(' ')
            mount_location = mtab_line_parts[1]
            fs_type = mtab_line_parts[2]
            if fs_type == 'tmpfs':
                mount_location = mount_location[1:]
                dir_path = os.path.join(mount_point, mount_location)
                if not os.path.exists(dir_path):
                    if self.euca.debug:
                        print 'Making essential directory %s' \
                            % mount_location
                    os.makedirs(dir_path)
        mtab_file.close()
        if pipe.returncode:

            # rsync return code 23: Partial transfer due to error
            # rsync return code 24: Partial transfer due to vanished source files

            if pipe.returncode in (23, 24):
                print 'Warning: rsync reports files partially copied:'
                print output
            else:
                print 'Error: rsync failed with return code %d' \
                    % pipe.returncode
                raise CopyError

    def unmount_image(self, mount_point):
        utils.check_prerequisite_command('umount')
        if self.euca.debug:
            print 'Unmounting image...'
        subprocess.Popen(['umount', '-d', mount_point],
                         stdout=subprocess.PIPE).communicate()[0]
        os.rmdir(mount_point)

    def copy_volume(self, image_path, volume_path, excludes,
                    generate_fstab, fstab_path):
        (mount_point, loop_dev) = self.mount_image(image_path)
        try:
            output = self.copy_to_image(mount_point, volume_path,
                    excludes)
            if self.img == 'Unsupported':
                print 'Platform not fully supported.'
                raise UnsupportedException
            self.img.add_fstab(mount_point, generate_fstab, fstab_path)
        except CopyError:
            raise CopyError
        finally:
            self.unmount_image(mount_point)
            
    def display_error_and_exit(self, msg):
        code = None
        message = None
        index = msg.find('<')
        if index < 0:
            print msg
            sys.exit(1)
        msg = msg[index - 1:]
        msg = msg.replace('\n', '')
        dom = minidom.parseString(msg)
        try:
            error_elem = dom.getElementsByTagName('Error')[0]
            code_elem = error_elem.getElementsByTagName('Code')[0]
            nodes = code_elem.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    code = node.data

            msg_elem = error_elem.getElementsByTagName('Message')[0]
            nodes = msg_elem.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    message = node.data

            print '%s:' % code, message
        except Exception:
            print msg
        sys.exit(1)

