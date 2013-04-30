# -*- coding: utf-8 -*-

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
# Author: David Kavanagh david.kavanagh@eucalyptus.com

import os
import sys
import tarfile
import hashlib
import re
import zlib
import shutil
import tempfile
import urllib2
import boto
import random
import time
from boto.roboto.param import Param
from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.roboto.awsqueryservice import AWSQueryService
from boto.s3.connection import Location
import euca2ools.bundler
import euca2ools.commands.eustore
import euca2ools.utils
from euca2ools.commands.euca.bundleimage import BundleImage
from euca2ools.commands.euca.uploadbundle import UploadBundle
from euca2ools.commands.euca.register import Register
from euca2ools.exceptions import NotFoundError, CommandFailed

try:
    import simplejson as json
except ImportError:
    import json

class LocalUploadBundle(UploadBundle):
    def process_cli_args(self):
        pass

class LocalRegister(Register):
    def process_cli_args(self):
        pass

class EuareService(AWSQueryService):
    Name = 'euare'
    Description = 'Eucalyptus IAM Service'
    APIVersion = '2010-05-08'
    Authentication = 'sign-v2'
    Path = '/'
    Port = 443
    Provider = 'aws'
    EnvURL = 'EUARE_URL'

class InstallImage(AWSQueryRequest):

    ServiceClass = euca2ools.commands.eustore.Eustore

    Description = """downloads and installs images from Eucalyptus.com"""
    Params = [
        Param(name='image_name',
              short_name='i',
              long_name='image_name',
              optional=True,
              ptype='string',
              doc="""name of image to install"""),
        Param(name='tarball',
              short_name='t',
              long_name='tarball',
              optional=True,
              ptype='string',
              doc="""name local image tarball to install from"""),
        Param(name='description',
              short_name='s',
              long_name='description',
              optional=True,
              ptype='string',
              doc="""description of image, mostly used with -t option"""),
        Param(name='architecture',
              short_name='a',
              long_name='architecture',
              optional=True,
              ptype='string',
              doc="""i386 or x86_64, mostly used with -t option"""),
        Param(name='prefix',
              short_name='p',
              long_name='prefix',
              optional=True,
              ptype='string',
              doc="""prefix to use when naming the image, mostly used with -t option"""),
        Param(name='bucket',
              short_name='b',
              long_name='bucket',
              optional=True,
              ptype='string',
              doc="""specify the bucket to store the images in"""),
        Param(name='kernel_type',
              short_name='k',
              long_name='kernel_type',
              optional=True,
              ptype='string',
              doc="""specify the type you're using [xen|kvm]"""),
        Param(name='dir',
              short_name='d',
              long_name='dir',
              optional=True,
              default='/tmp',
              ptype='string',
              doc="""specify a temporary directory for large files"""),
        Param(name='kernel',
              long_name='kernel',
              optional=True,
              ptype='string',
              doc="""Override bundled kernel with one already installed"""),
        Param(name='ramdisk',
              long_name='ramdisk',
              optional=True,
              ptype='string',
              doc="""Override bundled ramdisk with one already installed"""),
        Param(name='yes',
              short_name='y',
              long_name='yes',
              optional=True,
              ptype='boolean',
              doc="""Answer \"yes\" to questions during install"""),
        Param(name='bfebs_url',
              short_name='u',
              long_name='bfebs_url',
              optional=True,
              ptype='string',
              doc="""specify the URL to a BFEBS image to be registered"""),
        Param(name='volume_size',
              short_name='v',
              long_name='volume_size',
              optional=True,
              ptype='integer',
              doc="""specify the unapacked size BFEBS image to be registered (in GB)"""),
        Param(name='key',
              long_name='key',
              optional=True,
              ptype='string',
              doc="""specify the ssh key name to be used to spawn an instance""")
        ]
    ImageList = None

    def get_relative_filename(self, filename):
        return os.path.split(filename)[-1]

    def get_file_path(self, filename):
        relative_filename = self.get_relative_filename(filename)
        file_path = os.path.dirname(filename)
        if len(file_path) == 0:
            file_path = '.'
        return file_path

    def promptReplace(self, type, name):
        if self.cli_options.yes:
            print type+": "+name+" is already installed on the cloud, skipping installation of another one."
            return True
        else:
            answer = raw_input(type + ": " + name + " is already installed on this cloud. Would you like to use it instead? (y/N)")
            if (answer=='y' or answer=='Y'):
                return True
            return False

    def bundleFile(self, path, name, description, arch, kernel_id=None, ramdisk_id=None):
        bundler = euca2ools.bundler.Bundler(self)
        path = self.destination + path

        # before we do anything substantial, check to see if this "image" was already installed
        ret_id=None
        for img in self.ImageList:
            name_match=False
            if img.location.endswith(name+'.manifest.xml'):
                name_match=True
            # always replace skip if found
            if name_match:
                if kernel_id=='true' and img.type=='kernel':
                    if self.promptReplace("Kernel", img.name):
                        ret_id=img.id
                    break
                elif ramdisk_id=='true' and img.type=='ramdisk':
                    if self.promptReplace("Ramdisk", img.name):
                        ret_id=img.id
                    break
                elif kernel_id!='true' and ramdisk_id!='true' and img.type=='machine':
                    if self.promptReplace("Image", img.name):
                        ret_id=img.id
                    break

        if ret_id:
            return ret_id

        image_size = bundler.check_image(path, self.destination)
        try:
            (tgz_file, sha_tar_digest) = bundler.tarzip_image(name, path, self.destination)
        except (NotFoundError, CommandFailed):
            sys.exit(1)

        (encrypted_file, key, iv, bundled_size) = bundler.encrypt_image(tgz_file)
        os.remove(tgz_file)
        (parts, parts_digest) = bundler.split_image(encrypted_file)
        bundler.generate_manifest(self.destination, name,
                                  parts, parts_digest,
                                  path, key, iv,
                                  self.cert_path, self.ec2cert_path,
                                  self.private_key_path,
                                  arch, image_size,
                                  bundled_size, sha_tar_digest,
                                  self.user, kernel_id, ramdisk_id,
                                  None, None)
        os.remove(encrypted_file)

        obj = LocalUploadBundle()
        obj.bucket=self.cli_options.bucket
        obj.location=Location.DEFAULT
        obj.manifest_path=self.destination+name+".manifest.xml"
        obj.canned_acl='aws-exec-read'
        obj.bundle_path=None
        obj.skip_manifest=False
        obj.part=None
        obj.main()
        to_register = obj.bucket+'/'+self.get_relative_filename(obj.manifest_path)
        print to_register
        obj = LocalRegister()
        obj.image_location=to_register
        obj.name=name
        obj.description=description
        obj.snapshot=None
        obj.architecture=None
        obj.block_device_mapping=None
        obj.root_device_name=None
        obj.kernel=kernel_id
        obj.ramdisk=ramdisk_id
        return obj.main()

    def bundleAll(self, file, prefix, description, arch):
        print "Unbundling image"
        bundler = euca2ools.bundler.Bundler(self)
        try:
            names = bundler.untarzip_image(self.destination, file)
        except OSError:
            print >> sys.stderr, "Error: cannot unbundle image, possibly corrupted file"
            sys.exit(-1)
        except IOError:
            print >> sys.stderr, "Error: cannot unbundle image, possibly corrupted file"
            sys.exit(-1)
        kernel_dir=None
        if not(self.cli_options.kernel_type==None):
            kernel_dir = self.cli_options.kernel_type+'-kernel'
            print "going to look for kernel dir : "+kernel_dir
        #iterate, and install kernel/ramdisk first, store the ids
        kernel_id=self.cli_options.kernel
        ramdisk_id=self.cli_options.ramdisk
        kernel_found = False
        files_bundled = []
        if kernel_id==None:
            for i in [0, 1]:
                tar_root = os.path.commonprefix(names)
                for path in names:
                    if (kernel_dir==None or path.find(kernel_dir) > -1):
                        name = os.path.basename(path)
                        if not(kernel_dir) and (os.path.dirname(path) != tar_root):
                            continue;
                        if not name.startswith('.'):
                            # Note that vmlinuz is not always at the beginning of the filename
                            if name.find('vmlinu') != -1:
                                print "Bundling/uploading kernel"
                                if prefix:
                                    name = prefix+name
                                kernel_id = self.bundleFile(path, name, description, arch, 'true', None)
                                files_bundled.append(path)
                                kernel_found = True
                                print kernel_id
                            elif re.match(".*(initr(d|amfs)|loader).*", name):
                                print "Bundling/uploading ramdisk"
                                if prefix:
                                    name = prefix+name
                                ramdisk_id = self.bundleFile(path, name, description, arch, None, 'true')
                                files_bundled.append(path)
                                print ramdisk_id
                if not(kernel_found):
                    if not(kernel_dir):
                        print >> sys.stderr, "Error: couldn't find kernel. Check your parameters or specify an existing kernel/ramdisk"
                        sys.exit(-1);
                    elif i==0:
                        print >> sys.stderr, "Error: couldn't find kernel. Check your parameters or specify an existing kernel/ramdisk"
                        sys.exit(-1);
                else:
                    break
        #now, install the image, referencing the kernel/ramdisk
        image_id = None
        for path in names:
            name = os.path.basename(path)
            if not name.startswith('.'):
                if name.endswith('.img') and not(path in files_bundled):
                    print "Bundling/uploading image"
                    if prefix:
                        name = prefix
                    else:
                        name = name[:-len('.img')]
                    id = self.bundleFile(path, name, description, arch, kernel_id, ramdisk_id)
                    image_id = id
        # make good faith attempt to remove working directory and all files within
        shutil.rmtree(self.destination, True)
        return image_id

    def main(self, **args):
        self.process_args()
        self.cert_path = os.environ['EC2_CERT']
        self.private_key_path = os.environ['EC2_PRIVATE_KEY']
        self.user = os.environ['EC2_USER_ID']
        self.ec2cert_path = os.environ['EUCALYPTUS_CERT']

        if self.cli_options.bfebs_url:
            if (not self.cli_options.architecture or not (self.cli_options.architecture == 'i386' or\
                                                          self.cli_options.architecture == 'x86_64')):
                print >> sys.stderr, "Error: architecture must be either 'i386' or 'x86_64'"
                sys.exit(-1)
            if not self.cli_options.key:
                print >> sys.stderr, "Error: an ssh key name must be specified to create an EBS image"
                sys.exit(-1)
            if not self.cli_options.volume_size:
                self.cli_options.volume_size = 2
            if not self.cli_options.image_name:
                print >> sys.stderr, "Error: An image name is required when creating an EBS image"
                sys.exit(-1)
            if not self.cli_options.description:
                print >> sys.stderr, "Error: A description is required when creating an EBS image"
                sys.exit(-1)
                
        else:
          # tarball and image option are mutually exclusive
          if (not(self.cli_options.image_name) and not(self.cli_options.tarball)):
              print >> sys.stderr, "Error: one of -i or -t must be specified"
              sys.exit(-1)

          if (self.cli_options.image_name and self.cli_options.tarball):
              print >> sys.stderr, "Error: -i and -t cannot be specified together"
              sys.exit(-1)

          if (self.cli_options.tarball and \
              (not(self.cli_options.description) or not(self.cli_options.architecture))):
              print >> sys.stderr, "Error: when -t is specified, -s and -a are required"
              sys.exit(-1)

          if (self.cli_options.architecture and \
              not(self.cli_options.architecture == 'i386' or self.cli_options.architecture == 'x86_64')):
              print >> sys.stderr, "Error: architecture must be either 'i386' or 'x86_64'"
              sys.exit(-1)

          if (self.cli_options.kernel and not(self.cli_options.ramdisk)) or \
             (not(self.cli_options.kernel) and self.cli_options.ramdisk):
              print >> sys.stderr, "Error: kernel and ramdisk must both be overridden"
              sys.exit(-1)

          if (self.cli_options.architecture and self.cli_options.image_name):
              print >> sys.stderr, "Warning: you may be overriding the default architecture of this image!"

          if not self.cli_options.bucket:
              print >> sys.stderr, "Error: Required parameters are missing: (-b, --bucket)"
              sys.exit(-1)


        euare_svc = EuareService()
        conn = boto.connect_iam(host=euare_svc.args['host'], \
                    aws_access_key_id=euare_svc.args['aws_access_key_id'],\
                    aws_secret_access_key=euare_svc.args['aws_secret_access_key'],\
                    port=euare_svc.args['port'], path=euare_svc.args['path'],\
                    is_secure=euare_svc.args['is_secure'])
        conn.https_validate_certificates = False
        aliases = conn.get_account_alias()
        if not(aliases.list_account_aliases_result.account_aliases[0]=='eucalyptus') and not(self.cli_options.kernel):
            print >> sys.stderr, "Error: must be cloud admin to upload kernel/ramdisk. try specifying existing ones with --kernel and --ramdisk"
            sys.exit(-1)
        self.eustore_url = self.ServiceClass.StoreBaseURL

        # would be good of this were async, i.e. when the tarball is downloading
        ec2_conn = boto.connect_euca(host=euare_svc.args['host'], \
                        aws_access_key_id=euare_svc.args['aws_access_key_id'],\
                        aws_secret_access_key=euare_svc.args['aws_secret_access_key'])
        ec2_conn.APIVersion = '2012-03-01'
                        
        self.ImageList = ec2_conn.get_all_images()

        if self.cli_options.bfebs_url:
            #run first emi
            emi = None
            for i in range(0,len(self.ImageList)):
                #check to see if any images are named the same as that being passed
                if self.ImageList[i].name == self.cli_options.image_name:
                    print >> sys.stderr, "Error: an image already exists with the name you specified - please choose another."
                    sys.exit(-1)
                #only use an instance store image as we don't want an already attached EBS vol to deal with
                if self.ImageList[i].root_device_type != 'instance-store':
                    continue
                elif str(self.ImageList[i]).split(":")[1].startswith("emi"):
                  emi =  str(self.ImageList[i]).split(":")[1]
            if not emi:
                print >> sys.stderr, "Error: You just first register an instance-store image before importing an EBS image."
                sys.exit(-1)
            reservation = ec2_conn.run_instances(image_id=emi,key_name=self.cli_options.key)
            #we should have only one instance
            instance = reservation.instances[0]
            zones = ec2_conn.get_all_zones()
            zone = random.choice(zones).name
            #create 2 volumes - one to download the data to and one to be used for the EBS snapshot later
            volume1 = ec2_conn.create_volume(zone=zone,size=self.cli_options.volume_size + 1)
            volume2 = ec2_conn.create_volume(zone=zone,size=self.cli_options.volume_size)
            device_name1 = "/dev/vdb"
            device_name2 = "/dev/vdc"
            #make sure instance is running, timeout after 2 mins
            print "Waiting for instance to launch..."
            for i in range(0,120):
                if instance.state.lower() == "running": 
                    state = "running"
                    break
                else:
                    instance.update()
                    time.sleep(1)
                    continue
            if state == "pending":
                print >> sys.stderr, "Error: Instance failed to enter 'running' state."
                sys.exit(-1)
            #attach our volumes
            retval = ec2_conn.attach_volume(volume1.id,instance.id,device_name1)
            if not retval:
                print >> sys.stderr, "Error: Failed to attach newly created volume to instance at " + device_name1
                sys.exit(-1)
            retval = ec2_conn.attach_volume(volume2.id,instance.id,device_name2)
            if not retval:
                print >> sys.stderr, "Error: Failed to attach newly created volume to instance at " + device_name2
                sys.exit(-1)
            #locate the users' ssh key
            home_contents = os.listdir(os.path.expanduser('~'))
            keys = []
            for fname in home_contents:
                if fname.startswith(self.cli_options.key):
                    keys.append(fname)
            if len(keys) == 0: 
                print >> sys.stderr, "Error: Unable to find your ssh key in your home directory. Please place it there and name it "\
                                     + self.cli_options.key + ".priv" 
                sys.exit(-1)
            elif len(keys) > 1:
                print >> sys.stderr, "Error: Located multiple files beginning with your key name in your home directory"
                print >> sys.stderr, "Please ensure that your key is in your home directory and is the only file that begins with: "\
                                     + self.cli_options.key
                sys.exit(-1)
            key = keys[0] 
            #we need to ensure ssh has started and keys have been injected
            print "Waiting on volume attachment..."
            time.sleep(20)
            #format the volume where we will download the image to
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " mkfs.ext3 " + device_name1
            retval = os.system(cmd)
            if retval != 0:
                print >> sys.stderr, "Error: Failed to format the volume attached at " + device_name1
                sys.exit(-1)
            #mount the volume
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " mkdir /volume1"
            os.system(cmd)
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " mount -t ext3 " + device_name1 + " /volume1" 
            retval = os.system(cmd)
            if retval != 0:
                print >> sys.stderr, "Error: Failed to mount the volume attached at " + device_name1
                sys.exit(-1)
            #download the image
            image_fname = "/volume1/" + os.path.basename(self.cli_options.bfebs_url)
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " wget " + self.cli_options.bfebs_url + " -O " + image_fname
            print "Downloading the EBS image - this could take a while..."
            retval = os.system(cmd)
            if retval != 0:
                print >> sys.stderr, "Error: Failed to download image"
                sys.exit(-1)
            #write the image to the second volume
            print "Creating EBS volume - this may take a while..."
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " dd if=" + image_fname + " of=" + device_name2 + " bs=1M" 
            retval = os.system(cmd)
            if retval != 0:
                print >> sys.stderr, "Error: Failed to write image to volume"
                sys.exit(-1)
            #unmount volume1
            cmd = "ssh -i ~/" + key + " root@" + instance.ip_address + " umount /volume1"
            retval = os.system(cmd)
            if retval != 0:
                print >> sys.stderr, "Error: Failed to unmount volume (non-fatal)"
            #delete volume1
            retval = ec2_conn.detach_volume(volume1.id) 
            if not retval:
                print >> sys.stderr, "Error: Failed to delete volume (non-fatal)"
            else:
                print "Waiting for volume to detach..."
                while not volume1.status == "available":
                    time.sleep(5)
                    volume1.update()
                ec2_conn.delete_volume(volume1.id) 
            #take snapshot
            snapshot = ec2_conn.create_snapshot(volume2.id)
            print "Preparing snapshot - this will take some time..."
            while not snapshot.progress.startswith("100"):
                print "Progress: " + snapshot.progress
                snapshot.update()
                time.sleep(5)
            print "Successfully created snapshot: " + snapshot.id
            #delete volume2
            retval = ec2_conn.detach_volume(volume2.id) 
            if not retval:
                print >> sys.stderr, "Error: Failed to delete volume (non-fatal)"
            else:
                print "Waiting for volume to detach..."
                while not volume2.status == "available":
                    time.sleep(5)
                    volume2.update()
                ec2_conn.delete_volume(volume2.id) 
            obj = LocalRegister()
            obj.image_location=None
            obj.name=self.cli_options.image_name
            obj.description=self.cli_options.description
            obj.snapshot=snapshot.id
            obj.architecture=self.cli_options.architecture
            obj.block_device_mapping=[]
            obj.root_device_name="/dev/sda1"
            obj.kernel=None
            obj.ramdisk=None
            print "Successfully registered EBS image: " + obj.main()
            #terminate instance
            instance.terminate()
            
        else:
            if os.environ.has_key('EUSTORE_URL'):
                self.eustore_url = os.environ['EUSTORE_URL']

            self.destination = "/tmp/"
            if self.cli_options.dir:
                self.destination = self.cli_options.dir
            if not(self.destination.endswith('/')):
                self.destination += '/'
            # for security, add random directory within to work in
            self.destination = tempfile.mkdtemp(prefix=self.destination)+'/'

            if self.cli_options.tarball:
                # local tarball path instead
                print "Installed image: "+self.bundleAll(self.cli_options.tarball, self.cli_options.prefix, self.cli_options.description, self.cli_options.architecture)
            else:
                catURL = self.eustore_url + "catalog"
                req = urllib2.Request(catURL, headers=self.ServiceClass.RequestHeaders)
                response = urllib2.urlopen(req).read()
                parsed_cat = json.loads(response)
                if len(parsed_cat) > 0:
                    image_list = parsed_cat['images']
                    image_found = False
                    for image in image_list:
                        if image['name'].find(self.cli_options.image_name) > -1:
                            image_found = True
                            break
                    if image_found:
                        # more param checking now
                        if image['single-kernel']=='True':
                            if self.cli_options.kernel_type:
                                print >> sys.stderr, "The -k option will be ignored because the image is single-kernel"
                        else:
                            # Warn about kernel type for multi-kernel images, but not if already installed
                            # kernel/ramdisk have been specified.
                            if not(self.cli_options.kernel_type) and not(self.cli_options.kernel):
                                print >> sys.stderr, "Error: The -k option must be specified because this image has separate kernels"
                                sys.exit(-1)
                        print "Downloading Image : ",image['description']
                        imageURL = self.eustore_url+image['url']
                        req = urllib2.Request(imageURL, headers=self.ServiceClass.RequestHeaders)
                        req = urllib2.urlopen(req)
                        file_size = int(req.info()['Content-Length'])/1000
                        size_count = 0;
                        prog_bar = euca2ools.commands.eustore.progressBar(file_size)
                        BUF_SIZE = 128*1024
                        with open(self.destination+'eucaimage.tar.gz', 'wb') as fp:
                            while True:
                                buf = req.read(BUF_SIZE)
                                size_count += len(buf)
                                prog_bar.update(size_count/1000)
                                if not buf: break
                                fp.write(buf)
                        fp.close()
                        # validate download by re-computing serial # (name)
                        print "Checking image bundle"
                        file = open(fp.name, 'r')
                        m = hashlib.md5()
                        m.update(file.read())
                        hash = m.hexdigest()
                        crc = str(zlib.crc32(hash)& 0xffffffffL)
                        if image['name'] == crc.rjust(10,"0"):
                            print "Installed image: "+self.bundleAll(fp.name, None, image['description'], image['architecture'])
                        else:
                            print >> sys.stderr, "Error: Downloaded image was incomplete or corrupt, please try again"
                    else:
                        print >> sys.stderr, "Image name not found, please run eustore-describe-images"

    def main_cli(self):
        euca2ools.utils.print_version_if_necessary()
        self.debug=False
        self.do_cli()

