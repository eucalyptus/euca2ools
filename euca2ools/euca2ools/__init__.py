# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Eucalyptus Systems, Inc.
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

import boto
import getopt, sys, os
import tarfile
from xml.dom.minidom import Document
from xml.dom import minidom
from hashlib import sha1 as sha
from M2Crypto import BN, EVP, RSA, X509
from binascii import hexlify, unhexlify
from subprocess import *
import platform
import urllib
import re
import shutil
from boto.ec2.regioninfo import RegionInfo
import logging

BUNDLER_NAME = "euca-tools"
BUNDLER_VERSION = "1.2"
VERSION = "2007-10-10"
RELEASE = "31337"
AES = 'AES-128-CBC'

IP_PROTOCOLS = ['tcp', 'udp', 'icmp']

IMAGE_IO_CHUNK = 10 * 1024
IMAGE_SPLIT_CHUNK = IMAGE_IO_CHUNK * 1024;
MAX_LOOP_DEVS = 256;

METADATA_URL = "http://169.254.169.254/latest/meta-data/"

class LinuxImage:
    ALLOWED_FS_TYPES = ['ext2', 'ext3', 'xfs', 'jfs', 'reiserfs']
    BANNED_MOUNTS = ['/dev', '/media', '/mnt', '/proc', '/sys', '/cdrom', '/tmp']
    ESSENTIAL_DIRS = ['proc', 'tmp', 'dev', 'mnt', 'sys']
    ESSENTIAL_DEVS = [[os.path.join('dev', 'console'), 'c', '5', '1'],
		      [os.path.join('dev', 'full'), 'c', '1', '7'],
		      [os.path.join('dev', 'null'), 'c', '1', '3'],
		      [os.path.join('dev', 'zero'), 'c', '1', '5'],
		      [os.path.join('dev', 'tty'), 'c', '5', '0'],
		      [os.path.join('dev', 'tty0'), 'c', '4', '0'],
		      [os.path.join('dev', 'tty1'), 'c', '4', '1'],
 		      [os.path.join('dev', 'tty2'), 'c', '4', '2'],
 		      [os.path.join('dev', 'tty3'), 'c', '4', '3'],
 		      [os.path.join('dev', 'tty4'), 'c', '4', '4'],
 		      [os.path.join('dev', 'tty5'), 'c', '4', '5'],
		      [os.path.join('dev', 'xvc0'), 'c', '204', '191']]
    MAKEFS_CMD = 'mkfs.ext3'
    NEW_FSTAB = """
/dev/sda1 /     ext3    defaults 1 1
/dev/sdb  /mnt  ext3    defaults 0 0
none      /dev/pts devpts  gid=5,mode=620 0 0
none      /proc proc    defaults 0 0
none      /sys  sysfs   defaults 0 0
    """   

    OLD_FSTAB = """/dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
/dev/sda2	/mnt	      ext3     defaults			  0 0
/dev/sda3	swap	      swap     defaults			  0 0
proc            /proc         proc     defaults                   0 0
devpts          /dev/pts      devpts   gid=5,mode=620             0 0"""
 
    def __init__(self, debug=False):
	self.debug = debug
   
    def create_image(self, size_in_MB, image_path):
        dd_cmd = ["dd"] 
        dd_cmd.append("if=/dev/zero")
        dd_cmd.append("of=%s" % (image_path))
        dd_cmd.append("count=1")
        dd_cmd.append("bs=1M")
        dd_cmd.append("seek=%s" % (size_in_MB-1))
	if self.debug:
            print 'Creating disk image...', image_path
        Popen(dd_cmd, PIPE).communicate()[0]

    def make_fs(self, image_path):
        Util().check_prerequisite_command(self.MAKEFS_CMD)  

	if self.debug:
	    print "Creating filesystem..."
        makefs_cmd = Popen([self.MAKEFS_CMD, "-F", image_path], PIPE).communicate()[0]

    def add_fstab(self, mount_point, generate_fstab, fstab_path):
	if not fstab_path:
	    return
	fstab = None
	if fstab_path == "old":
	    if not generate_fstab:
		return
	    fstab = self.OLD_FSTAB
	elif fstab_path == "new":
	    if not generate_fstab:
		return
	    fstab = self.NEW_FSTAB

        etc_file_path = os.path.join(mount_point, "etc")
	fstab_file_path = os.path.join(etc_file_path, "fstab")
	if not os.path.exists(etc_file_path):
	    os.mkdir(etc_file_path)
	else:
	    if os.path.exists(fstab_file_path):
		fstab_copy_path = fstab_file_path + ".old"
		shutil.copyfile(fstab_file_path, fstab_copy_path)
   
	if self.debug:
	    print "Updating fstab entry" 
	fstab_file = open(fstab_file_path, "w")
	if fstab:
	    fstab_file.write(fstab)
	else:
	    orig_fstab_file = open(fstab_path, "r")
	    while 1:
		data = orig_fstab_file.read(IMAGE_IO_CHUNK)
		if not data:
		    break
		fstab_file.write(data)
	    orig_fstab_file.close()
	fstab_file.close()	

    def make_essential_devs(self, image_path):
	for entry in self.ESSENTIAL_DEVS:
	    cmd = ['mknod']
	    entry[0] = os.path.join(image_path, entry[0])
	    cmd.extend(entry)
            Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()

class SolarisImage:
    ALLOWED_FS_TYPES = ['ext2', 'ext3', 'xfs', 'jfs', 'reiserfs']
    BANNED_MOUNTS = ['/dev', '/media', '/mnt', '/proc', '/sys', '/cdrom', '/tmp']
    ESSENTIAL_DIRS = ['proc', 'tmp', 'dev', 'mnt', 'sys']

    def __init__(self, debug=False):
	self.debug = debug

    def create_image(self, size_in_MB, image_path):
	print "Sorry. Solaris not supported yet"
        raise UnsupportedException

    def make_fs(self, image_path):
	print "Sorry. Solaris not supported yet"
	raise UnsupportedException

    def make_essential_devs(self, image_path):
	print "Sorry. Solaris not supported yet"
	raise UnsupportedException

class Util:
    usage_string = """
-a, --access-key		User's Access Key ID.

-s, --secret-key		User's Secret Key.

-U, --url			URL of the Cloud to connect to.

--config			Read credentials and cloud settings from the 
				specified config file (defaults to $HOME/.eucarc or /etc/euca2ools/eucarc).

-h, --help			Display this help message.

--version 			Display the version of this tool.

--debug 			Turn on debugging.

Euca2ools will use the environment variables EC2_URL, EC2_ACCESS_KEY, EC2_SECRET_KEY, EC2_CERT, EC2_PRIVATE_KEY, S3_URL, EUCALYPTUS_CERT by default.
    """    

    version_string = """    Version: 1.2 (BSD)"""

    def version(self):
        return self.version_string
  
    def usage(self, compat=False):
	if compat:
	    self.usage_string = self.usage_string.replace("-s,", "-S,")
	    self.usage_string = self.usage_string.replace("-a,", "-A,")
    	print self.usage_string

    def check_prerequisite_command(self, command):
        cmd = [command]
	try:
            output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
	except OSError, e:
	    error_string = "%s" % e
	    if "No such" in error_string:
	        print "Command %s not found. Is it installed?" % command
	        raise NotFoundError
	    else:
	  	raise OSError(e)

class AddressValidationError:
    def __init__(self):
	self.message = 'Invalid address' 

class InstanceValidationError:
    def __init__(self):
	self.message = 'Invalid instance id'

class VolumeValidationError:
    def __init__(self):
	self.message = 'Invalid volume id'

class SizeValidationError:
    def __init__(self):
	self.message = 'Invalid size'

class SnapshotValidationError:
    def __init__(self):
	self.message = 'Invalid snapshot id'

class ProtocolValidationError:
    def __init__(self):
	self.message = 'Invalid protocol'

class FileValidationError:
    def __init__(self):
	self.message = 'Invalid file'

class DirValidationError:
    def __init__(self):
	self.message = 'Invalid directory'

class BundleValidationError:
    def __init__(self):
	self.message = 'Invalid bundle id'

class CopyError:
    def __init__(self):
	self.message = 'Unable to copy'

class MetadataReadError:
    def __init__(self):
	self.message = "Unable to read metadata"

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class NotFoundError:
    def __init__(self):
	self.message = "Unable to find"

class UnsupportedException:
    def __init__(self):
        self.message = "Not supported"

class CommandFailed:
    def __init__(self):
        self.message = "Command failed"
    
class ConnectionFailed:
    def __init__(self):
	self.message = "Connection failed"

class ParseError:
    def __init__(self, msg):
	self.message = msg

class Euca2ool:
 
 
    def process_args(self):
        ids = []
        for arg in self.args:
            ids.append(arg)
        return ids 


    def __init__(self, short_opts=None, long_opts=None, is_s3=False, compat=False):
	self.ec2_user_access_key = None
	self.ec2_user_secret_key = None
	self.ec2_url = None
	self.s3_url = None
	self.config_file_path = None
	self.is_s3 = is_s3
	if compat:
	    self.secret_key_opt = 'S'
	    self.access_key_opt = 'A'
	else:
	    self.secret_key_opt = 's'
	    self.access_key_opt = 'a'
	if not short_opts:
	    short_opts = ''
	if not long_opts:
	    long_opts = ['']
	short_opts += 'hU:'
	short_opts += '%s:' % self.secret_key_opt
	short_opts += '%s:' % self.access_key_opt
	long_opts += ['access-key=', 'secret-key=', 'url=', 'help', 'version', 'debug', 'config=']
        opts, args = getopt.gnu_getopt(sys.argv[1:], short_opts,
                                  long_opts)
	self.opts = opts
	self.args = args
	self.debug = False
        for name, value in opts:
            if name in ('-%s' % self.access_key_opt, '--access-key'):
 		self.ec2_user_access_key = value
	    elif name in ('-%s' % self.secret_key_opt, '--secret-key'):
		try:
		    self.ec2_user_secret_key = int(value)
		    self.ec2_user_secret_key = None
		except ValueError:
		    self.ec2_user_secret_key = value
	    elif name in ('-U', '--url'):
		self.ec2_url = value
	    elif name == '--debug':
		self.debug = True
 	    elif name == '--config':
		self.config_file_path = value
        system_string = platform.system()
	if system_string == "Linux":
	    self.img = LinuxImage(self.debug)
	elif system_string == "SunOS":
	    self.img = SolarisImage(self.debug)
	else:
	    self.img = "Unsupported"
        self.setup_environ()
    
        h = NullHandler()
        logging.getLogger("boto").addHandler(h)

    SYSTEM_EUCARC_PATH = os.path.join("/etc", "euca2ools", "eucarc")
    
    def setup_environ(self):
	envlist = ( 'EC2_ACCESS_KEY', 'EC2_SECRET_KEY', 'S3_URL', 'EC2_URL',
                 'EC2_CERT', 'EC2_PRIVATE_KEY', 'EUCALYPTUS_CERT',
                 'EC2_USER_ID' )
	self.environ = {}
	user_eucarc = None
	if 'HOME' in os.environ:
	    user_eucarc = os.path.join(os.getenv('HOME'), ".eucarc")
	read_config = False
	if self.config_file_path and os.path.exists(self.config_file_path):
	    read_config = self.config_file_path
	elif user_eucarc is not None and os.path.exists(user_eucarc):
	    read_config = user_eucarc
	elif os.path.exists(self.SYSTEM_EUCARC_PATH):
	    read_config = self.SYSTEM_EUCARC_PATH
	if read_config:	
            parse_config(read_config, self.environ, envlist)
    	else:
            for v in envlist:
                self.environ[v]=os.getenv(v)

    def get_environ(self, name):
	    if self.environ.has_key(name):
		return self.environ[name]
	    else:
		print '%s not found' % name
		raise NotFoundError

    def make_connection(self):
	if not self.ec2_user_access_key:
            self.ec2_user_access_key = self.environ['EC2_ACCESS_KEY']
 	    if not self.ec2_user_access_key:
                print 'EC2_ACCESS_KEY environment variable must be set.'
		raise ConnectionFailed
 
	if not self.ec2_user_secret_key:
            self.ec2_user_secret_key = self.environ['EC2_SECRET_KEY']
            if not self.ec2_user_secret_key:
                print 'EC2_SECRET_KEY environment variable must be set.'
		raise ConnectionFailed

        if not self.is_s3:
            if not self.ec2_url:
                self.ec2_url = self.environ['EC2_URL']
                if not self.ec2_url:
	            self.ec2_url = 'http://localhost:8773/services/Eucalyptus' 
    		    print 'EC2_URL not specified. Trying %s' % (self.ec2_url)
	else:
	    if not self.ec2_url:
                self.ec2_url = self.environ['S3_URL']
                if not self.ec2_url:
	            self.ec2_url = 'http://localhost:8773/services/Walrus' 
		    print 'S3_URL not specified. Trying %s' % (self.ec2_url)

        self.port = None
        self.service_path = "/" 
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
	        self.service_path = self.service_path + path_parts[1]
	    else:
		self.port = int(url_parts[1])

	if not self.is_s3:
     	    return boto.connect_ec2(aws_access_key_id=self.ec2_user_access_key, 
			        aws_secret_access_key=self.ec2_user_secret_key,
				is_secure=self.is_secure,
				region=RegionInfo(None, "eucalyptus", self.host),
				port=self.port,
				path=self.service_path)
	else:
	    return boto.s3.Connection(aws_access_key_id=self.ec2_user_access_key,
                            aws_secret_access_key=self.ec2_user_secret_key,
                            is_secure=self.is_secure,
                            host=self.host,
                            port=self.port,
			    calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                            path=self.service_path)

    def validate_address(self, address):
 	if not re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(\/[0-9]+)?$", address):
            raise AddressValidationError 

    def validate_instance_id(self, id):
 	if not re.match("i-", id):
            raise InstanceValidationError 

    def validate_volume_id(self, id):
 	if not re.match("vol-", id):
            raise VolumeValidationError 

    def validate_volume_size(self, size):
	if size < 0 or size > 1024:
	    raise SizeValidationError

    def validate_snapshot_id(self, id):
 	if not re.match("snap-", id):
            raise SnapshotValidationError 

    def validate_protocol(self, proto):
	if not proto in IP_PROTOCOLS:
	    raise ProtocolValidationError
	
    def validate_file(self, path):
	if not os.path.exists(path) or not os.path.isfile(path):
	    raise FileValidationError
	
    def validate_dir(self, path):
	if not os.path.exists(path) or not os.path.isdir(path):
	    raise DirValidationError
	
    def validate_bundle_id(self, id):
 	if not re.match("bun-", id):
            raise BundleValidationError 

    def get_relative_filename(self, filename):
        f_parts = filename.split('/')
        return f_parts[len(f_parts) - 1]

    def get_file_path(self, filename):
	relative_filename = self.get_relative_filename(filename)
	file_path=os.path.dirname(filename)
	if len(file_path) == 0:
	    file_path = "."
	return file_path

    def split_file(self, file, chunk_size):
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
	    print "Part:", self.get_relative_filename(filename)
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
        return parts, parts_digest
 
    def check_image(self, image_file, path):
        print 'Checking image'
        if not os.path.exists(path):
                os.makedirs(path)
        image_size = os.path.getsize(image_file)
	if self.debug:
	    print "Image Size:", image_size, "bytes"
        in_file = open(image_file, "rb")
        sha_image = sha()
        while 1:
                buf=in_file.read(IMAGE_IO_CHUNK)
                if not buf:
                   break
	sha_image.update(buf)
        return image_size, hexlify(sha_image.digest())

    def tarzip_image(self, prefix, file, path): 
        Util().check_prerequisite_command('tar')

        print 'Tarring image'
        tar_file = '%s.tar.gz' % os.path.join(path, prefix)
	outfile = open(tar_file, "wb")
	file_path = self.get_file_path(file)
	tar_cmd = ["tar", "c", "-S"]
	if file_path:
	    tar_cmd.append("-C")
	    tar_cmd.append(file_path)
	    tar_cmd.append(self.get_relative_filename(file))
	else:
	    tar_cmd.append(file)
        p1 = Popen(tar_cmd, stdout=PIPE)
	p2 = Popen(["gzip"], stdin=p1.stdout, stdout=outfile)
	p2.communicate()
	outfile.close
	if os.path.getsize(tar_file) <= 0:
	    print "Could not tar image"
            raise CommandFailed
        return tar_file

    def hexToBytes(self, hexString):
        bytes = []
        hexString = ''.join(hexString.split(" "))
        for i in range(0, len(hexString), 2):
                bytes.append(chr(int (hexString[i:i+2], 16)))

        return ''.join( bytes )

    def crypt_file(self, cipher, in_file, out_file) :
        while 1:
                buf=in_file.read(IMAGE_IO_CHUNK)
                if not buf:
                   break
                out_file.write(cipher.update(buf))
        out_file.write(cipher.final())
 
    def encrypt_image(self, file):
        print 'Encrypting image'
        enc_file = '%s.part' % (file.replace('.tar.gz', ''))

        key = (hex(BN.rand(16 * 8))[2:34]).replace('L', 'c')
	if self.debug:
            print 'Key: %s' % (key)
        iv = (hex(BN.rand(16 * 8))[2:34]).replace('L', 'c')
	if self.debug:
            print 'IV: %s' % (iv)

        k=EVP.Cipher(alg='aes_128_cbc', key=unhexlify(key), iv=unhexlify(iv), op=1)

        in_file = open(file)
        out_file = open(enc_file, "wb")
        self.crypt_file(k, in_file, out_file)
        in_file.close()
        out_file.close()
        bundled_size = os.path.getsize(enc_file)
        return enc_file, key, iv, bundled_size

    def split_image(self, file): 
        print 'Splitting image...'  
        return self.split_file(file, IMAGE_SPLIT_CHUNK) 

    def get_verification_string(self, manifest_string):
        start_mc = manifest_string.find('<machine_configuration>')
        end_mc = manifest_string.find('</machine_configuration>')
        mc_config_string = manifest_string[start_mc:end_mc + len('</machine_configuration>')]
        start_image = manifest_string.find('<image>')
        end_image = manifest_string.find('</image>')
        image_string = manifest_string[start_image:end_image + len('</image>')]

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
        encrypted_key_elem = manifest_elem.getElementsByTagName('user_encrypted_key')[0]
        nodes = encrypted_key_elem.childNodes
        for node in nodes:
	    if node.nodeType == node.TEXT_NODE:
	        encrypted_key = node.data
        encrypted_iv_elem = manifest_elem.getElementsByTagName('user_encrypted_iv')[0]
        nodes = encrypted_iv_elem.childNodes
        for node in nodes:
	    if node.nodeType == node.TEXT_NODE:
	        encrypted_iv = node.data
        return parts, encrypted_key, encrypted_iv

    def assemble_parts(self, src_directory, directory, manifest_path, parts):
        manifest_filename = self.get_relative_filename(manifest_path)
        encrypted_filename = os.path.join(directory, manifest_filename.replace('.manifest.xml', '.enc.tar.gz'))
        if (len(parts) > 0):
     	    if not os.path.exists(directory):
	        os.makedirs(directory)
	    encrypted_file = open(encrypted_filename, "wb")
	    for part in parts:
	        print "Part:", self.get_relative_filename(part)
		part_filename = os.path.join(src_directory, part)
	        part_file = open(part_filename, "rb")
	        while 1:
	            data = part_file.read(IMAGE_IO_CHUNK)
		    if not data:
		        break
		    encrypted_file.write(data)
	        part_file.close()			 
	    encrypted_file.close()
        return encrypted_filename

    def decrypt_image(self, encrypted_filename, encrypted_key, encrypted_iv, private_key_path):
        user_priv_key = RSA.load_key(private_key_path)
        key = user_priv_key.private_decrypt(unhexlify(encrypted_key), RSA.pkcs1_padding)
        iv = user_priv_key.private_decrypt(unhexlify(encrypted_iv), RSA.pkcs1_padding)
        k=EVP.Cipher(alg='aes_128_cbc', key=unhexlify(key), iv=unhexlify(iv), op=0)
  
        decrypted_filename = encrypted_filename.replace('.enc', '')
        decrypted_file = open(decrypted_filename, "wb")
        encrypted_file = open(encrypted_filename, "rb")
        self.crypt_file(k, encrypted_file, decrypted_file)
        encrypted_file.close()
        decrypted_file.close()
        return decrypted_filename

    def untarzip_image(self, path, file):
        untarred_filename = file.replace('.tar.gz', '') 
        tar_file = tarfile.open(file, "r|gz")
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

        return virtual, devices

    def generate_manifest(self, path, prefix, parts, parts_digest, file, key, iv, cert_path, ec2cert_path, private_key_path, target_arch, image_size, bundled_size, image_digest, user, kernel, ramdisk, mapping=None, product_codes=None, ancestor_ami_ids=None):
        user_pub_key = X509.load_cert(cert_path).get_pubkey().get_rsa()
        cloud_pub_key = X509.load_cert(ec2cert_path).get_pubkey().get_rsa()

        user_encrypted_key = hexlify(user_pub_key.public_encrypt(key, RSA.pkcs1_padding))
        user_encrypted_iv = hexlify(user_pub_key.public_encrypt(iv, RSA.pkcs1_padding))

        cloud_encrypted_key = hexlify(cloud_pub_key.public_encrypt(key, RSA.pkcs1_padding))
        cloud_encrypted_iv = hexlify(cloud_pub_key.public_encrypt(iv, RSA.pkcs1_padding))

        user_priv_key = RSA.load_key(private_key_path)

        manifest_file = '%s.manifest.xml' % os.path.join(path, prefix)
	if self.debug:
	    print 'Manifest: ', manifest_file

        print 'Generating manifest %s' % manifest_file

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
       	#release
	release_elem = doc.createElement("release")
	release_value = doc.createTextNode(RELEASE)
	release_elem.appendChild(release_value)
	bundler_elem.appendChild(release_elem)
        manifest_elem.appendChild(bundler_elem) 
 
        #machine config
        machine_config_elem = doc.createElement("machine_configuration")
        manifest_elem.appendChild(machine_config_elem)
        
        target_arch_elem = doc.createElement("architecture")
        target_arch_value = doc.createTextNode(target_arch)
        target_arch_elem.appendChild(target_arch_value)
        machine_config_elem.appendChild(target_arch_elem)
        
        #block device mapping
        if mapping:
            block_dev_mapping_elem = doc.createElement("block_device_mapping")
            virtual_names, device_names = self.get_block_devs(mapping)
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

        if product_codes:
            product_codes_elem = doc.createElement("product_codes")
            for product_code in product_codes:
	        product_code_elem = doc.createElement("product_code");
	        product_code_value = doc.createTextNode(product_code)
	        product_code_elem.appendChild(product_code_value)
	        product_codes_elem.appendChild(product_code_elem)
     	    machine_config_elem.appendChild(product_codes_elem)

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
        image_name_value = doc.createTextNode(self.get_relative_filename(file))
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

	#ancestor ami ids 
        if ancestor_ami_ids:
            ancestry_elem = doc.createElement("ancestry")
            for ancestor_ami_id in ancestor_ami_ids:
	        ancestor_id_elem = doc.createElement("ancestor_ami_id");
	        ancestor_id_value = doc.createTextNode(ancestor_ami_id)
	        ancestor_id_elem.appendChild(ancestor_id_value)
	        ancestry_elem.appendChild(ancestor_id_elem)
     	    image_elem.appendChild(ancestry_elem)

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
        image_elem.appendChild(cloud_encrypted_iv_elem)

        user_encrypted_iv_elem = doc.createElement("user_encrypted_iv")
        user_encrypted_iv_value = doc.createTextNode("%s" % (user_encrypted_iv))
        user_encrypted_iv_elem.appendChild(user_encrypted_iv_value)
        image_elem.appendChild(user_encrypted_iv_elem) 

        #parts
        parts_elem = doc.createElement("parts")
        parts_elem.setAttribute("count", '%s' % (len(parts)))
        part_number = 0
        for part in parts:
	    part_elem = doc.createElement("part")
	    filename_elem = doc.createElement("filename")
	    filename_value = doc.createTextNode(self.get_relative_filename(part))
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

        string_to_sign = self.get_verification_string(manifest_string)
        signature_elem = doc.createElement("signature")
        sha_manifest = sha()
        sha_manifest.update(string_to_sign)
        signature_value = doc.createTextNode("%s" % (hexlify(user_priv_key.sign(sha_manifest.digest()))))
        signature_elem.appendChild(signature_value)
        manifest_elem.appendChild(signature_elem)
        manifest_out_file.write(doc.toxml())
        manifest_out_file.close() 

    def add_excludes(self, path, excludes):
	if self.debug:
	    print "Reading /etc/mtab..."
        mtab_file = open("/etc/mtab", "r")
        while 1:
  	    mtab_line = mtab_file.readline()
	    if not mtab_line:
	        break
	    mtab_line_parts = mtab_line.split(' ')
	    mount_point = mtab_line_parts[1]
	    fs_type = mtab_line_parts[2]
	    if (mount_point.find(path) == 0) and (fs_type not in self.img.ALLOWED_FS_TYPES):
		if self.debug:
		    print 'Excluding %s...' % mount_point
	        excludes.append(mount_point)
	mtab_file.close()
        for banned in self.img.BANNED_MOUNTS:
	    excludes.append(banned)

    def make_image(self, size_in_MB, excludes, prefix, destination_path):
        image_file = '%s.img' % (prefix)
        image_path = '%s/%s' % (destination_path, image_file)
        if not os.path.exists(destination_path):
	    os.makedirs(destination_path)
 	if self.img == "Unsupported":
	    print "Platform not fully supported."
	    raise UnsupportedException
        self.img.create_image(size_in_MB, image_path)
        self.img.make_fs(image_path)        
        return image_path

    def create_loopback(self, image_path):
	Util().check_prerequisite_command('losetup')
	tries = 0
	while tries < MAX_LOOP_DEVS:
	    loop_dev = Popen(["losetup", "-f"], stdout=PIPE).communicate()[0].replace('\n', '')
	    if loop_dev:
	        output = Popen(["losetup", "%s" % loop_dev, "%s" % image_path], stdout=PIPE, stderr=PIPE).communicate()
	        if not output[1]:
		    return loop_dev
	    else:
		print "Could not create loopback device. Aborting"
		raise CommandFailed
	    tries += 1

    def mount_image(self, image_path):
        Util().check_prerequisite_command('mount') 

        tmp_mnt_point = "/tmp/%s" % (hex(BN.rand(16)))[2:6]
        if not os.path.exists(tmp_mnt_point):
	    os.makedirs(tmp_mnt_point)
	if self.debug:
	    print "Creating loopback device..."
        loop_dev = self.create_loopback(image_path)
	if self.debug:
	    print "Mounting image..."
        Popen(["mount", loop_dev, tmp_mnt_point], stdout=PIPE).communicate()  
        return tmp_mnt_point, loop_dev

    def copy_to_image(self, mount_point, volume_path, excludes):
	try:
	    Util().check_prerequisite_command('rsync')
	except NotFoundError:
	    raise CopyError
        rsync_cmd = ["rsync", "-aXS"]
        for exclude in excludes:
  	    rsync_cmd.append("--exclude")
	    rsync_cmd.append(exclude)
	rsync_cmd.append(volume_path)
	rsync_cmd.append(mount_point)
	if self.debug:
   	    print "Copying files..."
	    for exclude in excludes:
		print "Excluding:", exclude
        
        pipe = Popen(rsync_cmd, stdout=PIPE, stderr=PIPE)
        output = pipe.communicate()
        for dir in self.img.ESSENTIAL_DIRS:
            dir_path = os.path.join(mount_point, dir)
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
		if dir == "tmp":
		    os.chmod(dir_path, 01777)
	self.img.make_essential_devs(mount_point)
        mtab_file = open("/etc/mtab", "r")
        while 1:
  	    mtab_line = mtab_file.readline()
	    if not mtab_line:
	        break
	    mtab_line_parts = mtab_line.split(' ')
	    mount_location = mtab_line_parts[1]
	    fs_type = mtab_line_parts[2]
	    if fs_type == "tmpfs":
		mount_location = mount_location[1:]
	        dir_path = os.path.join(mount_point, mount_location)
		if not os.path.exists(dir_path):
		    if self.debug:
		        print 'Making essential directory %s' % mount_location 
		    os.makedirs(dir_path)	    
	mtab_file.close()
	if pipe.returncode:
            # rsync return code 23: Partial transfer due to error
            # rsync return code 24: Partial transfer due to vanished source files
            if pipe.returncode in (23, 24):
                print "Warning: rsync reports files partially copied:"
                print output
            else:
                print "Error: rsync failed with return code %d" % pipe.returncode
                raise CopyError

    def unmount_image(self, mount_point):
        Util().check_prerequisite_command('umount') 
	if self.debug:
	    print "Unmounting image..."
        Popen(["umount", "-d", mount_point], stdout=PIPE).communicate()[0]
        os.rmdir(mount_point)

    def copy_volume(self, image_path, volume_path, excludes, generate_fstab, fstab_path):
        mount_point, loop_dev = self.mount_image(image_path)
	try:
            output = self.copy_to_image(mount_point, volume_path, excludes)
   	    if self.img == "Unsupported":
	        print "Platform not fully supported."
		raise UnsupportedException
	    self.img.add_fstab(mount_point, generate_fstab, fstab_path)
	except CopyError:
	    raise CopyError 
	finally:
            self.unmount_image(mount_point)

    def can_read_instance_metadata(self):
        meta_data = urllib.urlopen(METADATA_URL)        

    def get_instance_metadata(self, type):
        if self.debug:
	    print "Reading instance metadata", type
        metadata = urllib.urlopen(METADATA_URL + type).read()
	if "Not" in metadata and "Found" in metadata and "404" in metadata:
	    raise MetadataReadError
	return metadata

    def get_instance_ramdisk(self):
        return self.get_instance_metadata('ramdisk-id')

    def get_instance_kernel(self):
        return self.get_instance_metadata('kernel-id')

    def get_instance_product_codes(self):
        return self.get_instance_metadata('product-codes')

    def get_ancestor_ami_ids(self):
        return self.get_instance_metadata('ancestor-ami-ids')

    def get_instance_block_device_mappings(self):
        keys = self.get_instance_metadata('block-device-mapping').split('\n')
        mapping = []
        for k in keys:
            mapping.append(k)
            mapping.append(self.get_instance_metadata(os.path.join('block-device-mapping', k)))
        return mapping

    def display_error_and_exit(self, msg):
	code = None
	message = None
	index = msg.find("<")
	if (index < 0):
	    print msg
	    sys.exit(1) 
	msg = msg[index-1:]
	msg = msg.replace("\n", "")
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

 	    print "%s:" % code, message
	except Exception:
	    print msg
	sys.exit(1)

# read the config file 'config', update 'dict', setting 
# the value from the config file for each element in array 'keylist'
# "config" is a bash syntax file defining bash variables
def parse_config(config, dict, keylist):
    fmt = ""
    str=""
    for v in keylist:
        str='%s "${%s}" ' % (str, v)
        fmt=fmt + "%s%s" % ("%s", "\\0")

    cmd = [ "bash", "-ec", 
            ". '%s' >/dev/null; printf '%s' %s" \
            % ( config, fmt, str ) ]
    
    handle = Popen(cmd, stderr=PIPE, stdout=PIPE)
    ( stdout, stderr) = handle.communicate()
    if handle.returncode != 0:
        raise ParseError("Parsing config file %s failed:\n\t%s" %(config, stderr))

    values = stdout.split("\0")
    for i in range(len(values) - 1):
        if values[i] != "":
            dict[keylist[i]]=values[i]
