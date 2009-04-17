# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Regents of the University of California
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
# Author: Sunil Soman sunils@cs.ucsb.edu

import boto
import getopt, sys, os
import tarfile
import gzip
from xml.dom.minidom import Document
from hashlib import sha1 as sha
from M2Crypto import BN, EVP, RSA, util, Rand, m2, X509
from binascii import hexlify, unhexlify
from subprocess import *

VERSION = "2007-10-10"
BUNDLER_NAME = "euca-tools"
BUNDLER_VERSION = "1.0"
AES = 'AES-128-CBC'

MAKEFS_CMD = 'mkfs.ext2'

usage_string = """
	-K, --access-key - user's Access Key ID.
 	-S, --secret-key - user's Secret Key.
	-U, --url - Cloud URL.
	-h, --help - Display this help message.
	--version - Display the version of this tool.
	--debug - Turn on debugging.
"""     
IMAGE_IO_CHUNK = 8 * 1024
IMAGE_SPLIT_CHUNK = IMAGE_IO_CHUNK * 1024;

#This needs to refactored into platform dependent libs
ALLOWED_FS_TYPES = ['ext2', 'ext3', 'xfs', 'jfs', 'reiserfs']
BANNED_MOUNTS = ['/dev', '/media', '/mnt', '/proc', '/sys']
def usage():
    print usage_string
    sys.exit()


class EucaTool:
    def process_args(self):
        ids = []
        for arg in self.args:
            ids.append(arg)
        return ids 

    def __init__(self, short_opts=None, long_opts=None, is_s3=False):

	self.ec2_user_access_key = None
	self.ec2_user_secret_key = None
	self.ec2_url = None
	self.s3_url = None
	self.is_s3 = is_s3
	if not short_opts:
	    short_opts = ''
	if not long_opts:
	    long_opts = ['']
	short_opts += 'hK:S:U:'
	long_opts += ['access-key=', 'secret-key=', 'url=', 'help', 'version', 'debug']
        opts, args = getopt.getopt(sys.argv[1:], short_opts,
                                  long_opts)
	self.opts = opts
	self.args = args
        for name, value in opts:
            if name in ('-K', '--access-key'):
 		self.ec2_user_access_key = value
	    elif name in ('-S', '--secret-key'):
		self.ec2_user_secret_key = value
	    elif name in ('-U', '--url'):
		self.ec2_url = value
	    elif name in ('--debug'):
		self.debug = True
        
	if not self.ec2_user_access_key:
            self.ec2_user_access_key = os.getenv('EC2_ACCESS_KEY')
 	    if not self.ec2_user_access_key:
                print 'EC2_ACCESS_KEY environment variable must be set.'
     		sys.exit()
 
	if not self.ec2_user_secret_key:
            self.ec2_user_secret_key = os.getenv('EC2_SECRET_KEY')
            if not self.ec2_user_secret_key:
                print 'EC2_SECRET_KEY environment variable must be set.'
		sys.exit()

        if not self.is_s3:
            if not self.ec2_url:
                self.ec2_url = os.getenv('EC2_URL')
                if not self.ec2_url:
	            self.ec2_url = 'http://localhost:8773/services/Eucalyptus' 
    		    print 'EC2_URL not specified. Trying %s' % (self.ec2_url)
	else:
	    if not self.ec2_url:
                self.ec2_url = os.getenv('S3_URL')
                if not self.ec2_url:
	            self.ec2_url = 'http://localhost:8773/services/Walrus' 
		    print 'S3_URL not specified. Trying %s' % (self.ec2_url)

        self.port = None
        self.service_path = '/'
	if (self.ec2_url.find('https://') >= 0):
            self.ec2_url = self.ec2_url.replace('https://', '')
	    self.is_secure = True
 	else:
            self.ec2_url = self.ec2_url.replace('http://', '')
	    self.is_secure = False
        self.host = self.ec2_url 
        url_parts = self.ec2_url.split(':')
        if (len(url_parts) > 1):
            self.host = url_parts[0]
            path_parts = url_parts[1].split('/', 1)
    	    if (len(path_parts) > 1):
	        self.port = int(path_parts[0])
	        self.service_path = path_parts[1]
	    else:
		self.port = int(url_parts[1])

    def make_connection(self):
	if not self.is_s3:
            return boto.connect_ec2(aws_access_key_id=self.ec2_user_access_key, 
			        aws_secret_access_key=self.ec2_user_secret_key,
				is_secure=self.is_secure,
				host=self.host,
				port=self.port,
				service=self.service_path)
	else:
	    return boto.s3.Connection(aws_access_key_id=self.ec2_user_access_key,
                            aws_secret_access_key=self.ec2_user_secret_key,
                            is_secure=self.is_secure,
                            host=self.host,
                            port=self.port,
                            service=self.service_path)

def get_absolute_filename(filename):
    f_parts = filename.split('/')
    return f_parts[len(f_parts) - 1]

def split_file(file, chunk_size):
    parts = []
    parts_digest = []
    file_size = os.path.getsize(file)
    in_file = open(file, "rb")
    number_parts = int(file_size / chunk_size)
    number_parts += 1
    bytes_read = 0
    for i in range(0, number_parts, 1):
	filename = '%s.%d' % (file, i)
	part_digest = sha()
	file_part = open(filename, "wb")
	part_bytes_written = 0
	while part_bytes_written < IMAGE_SPLIT_CHUNK:
	    data = in_file.read(IMAGE_IO_CHUNK)
	    file_part.write(data)
	    part_digest.update(data)
	    data_len = len(data)
	    part_bytes_written += data_len    	    		
	    bytes_read += data_len
	    if bytes_read >= file_size: break
	file_part.close()
	parts.append(filename)
	parts_digest.append(hexlify(part_digest.digest()))	

    in_file.close()
    return parts, parts_digest
 
def check_image(image_file, path):
    print 'checking image'
    if not os.path.exists(path):
        os.makedirs(path)
    image_size = os.path.getsize(image_file)
    in_file = open(image_file, "rb")
    sha_image = sha()
    while 1:
        buf=in_file.read(IMAGE_IO_CHUNK)
        if not buf:
           break
	sha_image.update(buf)
    return image_size, hexlify(sha_image.digest())

def tar_image(prefix, file, path): 
    print 'tarring image'
    tar_file = '%s.tar' % (path + '/' + prefix) 
    tar = tarfile.open(tar_file, "w")
    tar.add(file)
    tar.close()
    return tar_file

def zip_image(file):
    print 'zipping image'
    file_in = open(file, 'rb')
    gz_file = '%s.gz' % (file)
    gz_out = gzip.open(gz_file, 'wb')
    gz_out.writelines(file_in)
    gz_out.close()
    file_in.close()
    return gz_file

def hexToBytes(hexString):
    bytes = []
    hexString = ''.join(hexString.split(" "))
    for i in range(0, len(hexString), 2):
        bytes.append(chr(int (hexString[i:i+2], 16)))

    return ''.join( bytes )

def encrypt_file(cipher, in_file, out_file) :
    while 1:
        buf=in_file.read(IMAGE_IO_CHUNK)
        if not buf:
           break
        out_file.write(cipher.update(buf))
    out_file.write(cipher.final())
  

def decrypt_file( cipherType, key, iv, in_file, out_file ) :
    dec = DecryptCipher( cipherType, key, iv )
    while 1 :
        data = in_file.read(IMAGE_IO_CHUNK)
        if not data : break
        out_data = dec.update( data )
        out_file.write( out_data )
    final_data = dec.finish()
    out_file.write( final_data )
 
def encrypt_image(file):
    print 'encrypting image'
    enc_file = '%s.part' % (file.replace('.tar.gz', ''))

    key = (hex(BN.rand(16 * 8))[2:34]).replace('L', 'c')
    print 'key: %s' % (key)
    iv = (hex(BN.rand(16 * 8))[2:34]).replace('L', 'c')
    print 'iv: %s' % (iv)

    k=EVP.Cipher(alg='aes_128_cbc', key=unhexlify(key), iv=unhexlify(iv), op=1)

    in_file = open(file)
    out_file = open(enc_file, "wb")
    encrypt_file(k, in_file, out_file)
    in_file.close()
    out_file.close()
    bundled_size = os.path.getsize(enc_file)
    return enc_file, key, iv, bundled_size

def split_image(file): 
    print 'splitting image'  
    return split_file(file, IMAGE_SPLIT_CHUNK) 

def get_verification_string(manifest_string):
    start_mc = manifest_string.find('<machine_configuration>')
    end_mc = manifest_string.find('</machine_configuration>')
    mc_config_string = manifest_string[start_mc:end_mc + len('</machine_configuration>')]
    start_image = manifest_string.find('<image>')
    end_image = manifest_string.find('</image>')
    image_string = manifest_string[start_image:end_image + len('</image>')]

    return mc_config_string + image_string

def get_block_devs(mapping):
    virtual = []
    devices = []
   
    mapping_pairs = mapping.split(',')
    for m in mapping_pairs:
 	m_parts = m.split('=')
        if(len(m_parts) > 1):
	    virtual.append(m_parts[0])
	    devices.append(m_parts[1])
  
    return virtual, devices

def generate_manifest(path, prefix, parts, parts_digest, file, key, iv, cert_path, ec2cert_path, private_key_path, target_arch, image_size, bundled_size, image_digest, user, kernel, ramdisk, mapping):
    print 'generating manifest'

    user_pub_key = X509.load_cert(cert_path).get_pubkey().get_rsa()
    cloud_pub_key = X509.load_cert(ec2cert_path).get_pubkey().get_rsa()

    user_encrypted_key = hexlify(user_pub_key.public_encrypt(key, RSA.pkcs1_padding))
    user_encrypted_iv = hexlify(user_pub_key.public_encrypt(iv, RSA.pkcs1_padding))

    cloud_encrypted_key = hexlify(cloud_pub_key.public_encrypt(key, RSA.pkcs1_padding))
    cloud_encrypted_iv = hexlify(cloud_pub_key.public_encrypt(iv, RSA.pkcs1_padding))

    user_priv_key = RSA.load_key(private_key_path)

    manifest_file = '%s.manifest.xml' % (path + "/" + prefix)
    manifest_out_file = open(manifest_file, "wb")
    doc = Document()
    
    manifest_elem = doc.createElement("manifest")
    doc.appendChild(manifest_elem)

    #version
    version_elem = doc.createElement("version")
    version_value = doc.createTextNode(VERSION)
    version_elem.appendChild(version_value)
    manifest_elem.appendChild(version_elem)
 
    #bundler info
    bundler_elem = doc.createElement("bundler")
    bundler_name_elem = doc.createElement("name")
    bundler_name_value = doc.createTextNode(BUNDLER_NAME)
    bundler_name_elem.appendChild(bundler_name_value)
    bundler_version_elem = doc.createElement("version")
    bundler_version_value = doc.createTextNode(BUNDLER_VERSION)
    bundler_version_elem.appendChild(bundler_version_value)
    bundler_elem.appendChild(bundler_name_elem)
    bundler_elem.appendChild(bundler_version_elem)
    manifest_elem.appendChild(bundler_elem) 

    #machine config
    machine_config_elem = doc.createElement("machine_configuration")
    manifest_elem.appendChild(machine_config_elem)
    
    target_arch_elem = doc.createElement("architecture")
    target_arch_value = doc.createTextNode(target_arch)
    target_arch_elem.appendChild(target_arch_value)
    machine_config_elem.appendChild(target_arch_elem)
    
    #block device mapping
    block_dev_mapping_elem = doc.createElement("block_device_mapping")
    if mapping:
        virtual_names, device_names = get_block_devs(mapping)
        vname_index = 0
        for vname in virtual_names:
	    dname = device_names[vname_index]
            mapping_elem = doc.createElement("mapping")
            virtual_elem = doc.createElement("virtual")
            virtual_value = doc.createTextNode(vname)
            virtual_elem.appendChild(virtual_value)
            mapping_elem.appendChild(virtual_elem)
            device_elem = doc.createElement("device")
       	    device_value = doc.createTextNode(dname)
   	    device_elem.appendChild(device_value)
	    mapping_elem.appendChild(device_elem)
	    block_dev_mapping_elem.appendChild(mapping_elem)
	    vname_index = vname_index + 1
	
        machine_config_elem.appendChild(block_dev_mapping_elem)

    #kernel and ramdisk
    if kernel:
	kernel_id_elem = doc.createElement("kernel_id")
	kernel_id_value = doc.createTextNode(kernel)
	kernel_id_elem.appendChild(kernel_id_value)
	machine_config_elem.appendChild(kernel_id_elem)

    if ramdisk:
	ramdisk_id_elem = doc.createElement("ramdisk_id")
	ramdisk_id_value = doc.createTextNode(ramdisk)
	ramdisk_id_elem.appendChild(ramdisk_id_value)
	machine_config_elem.appendChild(ramdisk_id_elem)

    image_elem = doc.createElement("image")
    manifest_elem.appendChild(image_elem)

    #name
    image_name_elem = doc.createElement("name") 
    image_name_value = doc.createTextNode(get_absolute_filename(file))
    image_name_elem.appendChild(image_name_value)
    image_elem.appendChild(image_name_elem)
 
    #user
    user_elem = doc.createElement("user")
    user_value = doc.createTextNode("%s" % (user))
    user_elem.appendChild(user_value)
    image_elem.appendChild(user_elem)
    
    #type
    #TODO: fixme
    image_type_elem = doc.createElement("type")
    image_type_value = doc.createTextNode("machine")
    image_type_elem.appendChild(image_type_value)
    image_elem.appendChild(image_type_elem) 
    
    #digest
    image_digest_elem = doc.createElement("digest")
    image_digest_elem.setAttribute('algorithm', 'SHA1')
    image_digest_value = doc.createTextNode('%s' % (image_digest))
    image_digest_elem.appendChild(image_digest_value)
    image_elem.appendChild(image_digest_elem) 
    
    #size
    image_size_elem = doc.createElement("size")
    image_size_value = doc.createTextNode("%s" % (image_size))
    image_size_elem.appendChild(image_size_value)
    image_elem.appendChild(image_size_elem)

    #bundled size
    bundled_size_elem = doc.createElement("bundled_size")
    bundled_size_value = doc.createTextNode("%s" % (bundled_size))
    bundled_size_elem.appendChild(bundled_size_value)
    image_elem.appendChild(bundled_size_elem)

    #key, iv
    cloud_encrypted_key_elem = doc.createElement("ec2_encrypted_key")
    cloud_encrypted_key_value = doc.createTextNode("%s" % (cloud_encrypted_key))
    cloud_encrypted_key_elem.appendChild(cloud_encrypted_key_value)
    cloud_encrypted_key_elem.setAttribute("algorithm", AES)
    image_elem.appendChild(cloud_encrypted_key_elem)
    
    user_encrypted_key_elem = doc.createElement("user_encrypted_key")
    user_encrypted_key_value = doc.createTextNode("%s" % (user_encrypted_key))
    user_encrypted_key_elem.appendChild(user_encrypted_key_value)
    user_encrypted_key_elem.setAttribute("algorithm", AES)
    image_elem.appendChild(user_encrypted_key_elem) 

    cloud_encrypted_iv_elem = doc.createElement("ec2_encrypted_iv")
    cloud_encrypted_iv_value = doc.createTextNode("%s" % (cloud_encrypted_iv))
    cloud_encrypted_iv_elem.appendChild(cloud_encrypted_iv_value)
    cloud_encrypted_iv_elem.setAttribute("algorithm", AES)
    image_elem.appendChild(cloud_encrypted_iv_elem)

    user_encrypted_iv_elem = doc.createElement("user_encrypted_iv")
    user_encrypted_iv_value = doc.createTextNode("%s" % (user_encrypted_iv))
    user_encrypted_iv_elem.appendChild(user_encrypted_iv_value)
    user_encrypted_iv_elem.setAttribute("algorithm", AES)
    image_elem.appendChild(user_encrypted_iv_elem) 

    #parts
    parts_elem = doc.createElement("parts")
    parts_elem.setAttribute("count", '%s' % (len(parts)))
    part_number = 0
    for part in parts:
	part_elem = doc.createElement("part")
	filename_elem = doc.createElement("filename")
	filename_value = doc.createTextNode(get_absolute_filename(part))
	filename_elem.appendChild(filename_value)
	part_elem.appendChild(filename_elem)
        #digest
	part_digest_elem = doc.createElement("digest")
	part_digest_elem.setAttribute('algorithm', 'SHA1')
	part_digest_value = doc.createTextNode(parts_digest[part_number])
	part_digest_elem.appendChild(part_digest_value)
	part_elem.appendChild(part_digest_elem)
	part_elem.setAttribute("index", '%s' % (part_number))
	parts_elem.appendChild(part_elem)
        part_number += 1
    image_elem.appendChild(parts_elem)

    manifest_string = doc.toxml()

    string_to_sign = get_verification_string(manifest_string)
    signature_elem = doc.createElement("signature")
    sha_manifest = sha()
    sha_manifest.update(string_to_sign)
    signature_value = doc.createTextNode("%s" % (hexlify(user_priv_key.sign(sha_manifest.digest()))))
    signature_elem.appendChild(signature_value)
    manifest_elem.appendChild(signature_elem)
    manifest_out_file.write(doc.toxml())
    manifest_out_file.close() 

def add_excludes(path, excludes):
    mtab_file = open("/etc/mtab", "r")
    while 1:
	mtab_line = mtab_file.readline()
	if not mtab_line:
	    break
	mtab_line_parts = mtab_line.split(' ')
	mount_point = mtab_line_parts[1]
	fs_type = mtab_line_parts[2]
	if (mount_point.find(path) == 0) and (fs_type not in ALLOWED_FS_TYPES):
	    excludes.append(mount_point)

def create_image(size_in_MB, image_path):
    dd_cmd = ["dd"] 
    dd_cmd.append("if=/dev/zero")
    dd_cmd.append("of=%s" % (image_path))
    dd_cmd.append("count=%d" % (size_in_MB))
    dd_cmd.append("bs=1M")
    print Popen(dd_cmd, PIPE).communicate()[0]

def make_fs(image_path):
    makefs_cmd = Popen([MAKEFS_CMD, "-F", image_path], PIPE).communicate()[0]

def make_image(size_in_MB, excludes, prefix, destination_path):
    image_file = '%s.img' % (prefix)
    image_path = '%s/%s' % (destination_path, image_file)
    create_image(size_in_MB, image_path)
    make_fs(image_path)    
    return image_path

def create_loopback(image_path):
    return Popen(["losetup", "-sf", ('%s' % (image_path))], stdout=PIPE).communicate()[0].replace('\n', '')

def mount_image(image_path):
    tmp_mnt_point = "/tmp/%s" % (hex(BN.rand(16)))[2:6]
    if not os.path.exists(tmp_mnt_point):
	os.makedirs(tmp_mnt_point)
    loop_dev = create_loopback(image_path)
    Popen(["mount", loop_dev, tmp_mnt_point], stdout=PIPE).communicate()  
    return tmp_mnt_point, loop_dev

def copy_to_image(mount_point, volume_path, excludes):
    Popen(["rsync", "-r", volume_path, mount_point], stdout=PIPE).communicate()

def unmount_image(mount_point):
    Popen(["umount", "-d", mount_point], stdout=PIPE).communicate()
    os.rmdir(mount_point)

def copy_volume(image_path, volume_path, excludes):
    mount_point, loop_dev = mount_image(image_path)
    copy_to_image(mount_point, volume_path, excludes)
    unmount_image(mount_point)
