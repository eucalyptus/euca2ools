#!/usr/local/bin/python
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
import urllib2
from boto.roboto.param import Param
from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.s3.connection import Location
import euca2ools.bundler
import euca2ools.commands.eustore
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

class InstallImage(AWSQueryRequest):

    ServiceClass = euca2ools.commands.eustore.Eustore

    Description = """downloads and installs images from Eucalyptus.com"""
    Params = [
        Param(name='image_name',
              short_name='i',
              long_name='image_name',
              optional=False,
              ptype='string',
              doc="""name of image to install"""),
        Param(name='bucket',
              short_name='b',
              long_name='bucket',
              optional=False,
              ptype='string',
              doc="""specify the bucket to store the images in"""),
        Param(name='kernel_type',
              short_name='k',
              long_name='kernel_type',
              optional=False,
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
              doc="""Override bundled ramdisk with one already installed""")
        ]


    def get_relative_filename(self, filename):
        return os.path.split(filename)[-1]

    def get_file_path(self, filename):
        relative_filename = self.get_relative_filename(filename)
        file_path = os.path.dirname(filename)
        if len(file_path) == 0:
            file_path = '.'
        return file_path

    def bundleFile(self, path, name, image, kernel_id=None, ramdisk_id=None):
        bundler = euca2ools.bundler.Bundler(self)
        path = self.destination + path

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
                                  image['architecture'], image_size,
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
        obj.description=image['description']
        obj.snapshot=None
        obj.architecture=None
        obj.block_device_mapping=None
        obj.root_device_name=None
        obj.kernel=kernel_id
        obj.ramdisk=ramdisk_id
        return obj.main()

    def bundleAll(self, file, image):
        print "Unwrapping tarball"
        bundler = euca2ools.bundler.Bundler(self)
        names = bundler.untarzip_image(self.destination, file)
        kernel_dir = self.cli_options.kernel_type+'-kernel'
        #iterate, and install kernel/ramdisk first, store the ids
        kernel_id=self.cli_options.kernel
        ramdisk_id=self.cli_options.ramdisk
        if kernel_id==None:
            for path in names:
                if path.find(kernel_dir) > -1:
                    name = os.path.basename(path)
                    if not name.startswith('.'):
                        if name.startswith('vmlin'):
                            print "Bundling/uploading kernel"
                            kernel_id = self.bundleFile(path, name, image, 'true', None)
                            print kernel_id
                        elif name.startswith('initrd'):
                            print "Bundling/uploading ramdisk"
                            ramdisk_id = self.bundleFile(path, name, image, None, 'true')
                            print ramdisk_id
        #now, install the image, referencing the kernel/ramdisk
        for path in names:
            name = os.path.basename(path)
            if not name.startswith('.'):
                if name.endswith('.img'):
                    print "Bundling/uploading image"
                    name = name[:-len('.img')]
                    id = self.bundleFile(path, name, image, kernel_id, ramdisk_id)
                    return id

    def main(self, **args):
        self.process_args()
        if (self.cli_options.kernel and not(self.cli_options.ramdisk)) or \
           (not(self.cli_options.kernel) and self.cli_options.ramdisk):
            print "Error: kernel and ramdisk must both be overrided"
            sys.exit(-1)

        self.eustore_url = self.ServiceClass.StoreBaseURL
        if os.environ.has_key('EUSTORE_URL'):
            self.eustore_url = os.environ['EUSTORE_URL']

        self.destination = "/tmp/"
        if self.cli_options.dir:
            self.destination = self.cli_options.dir
        if not(self.destination.endswith('/')):
            self.destination += '/'

        catURL = self.eustore_url + "catalog.json"
        response = urllib2.urlopen(catURL).read()
        parsed_cat = json.loads(response)
        if len(parsed_cat) > 0:
            image_list = parsed_cat['images']
            image_found = False
            for image in image_list:
                if image['name'].find(self.cli_options.image_name) > -1:
                   image_found = True
                   break
            if image_found:
                print "Downloading Image : ",image['description']
                imageURL = self.ServiceClass.StoreBaseURL+image['url']
                req = urllib2.urlopen(imageURL)
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
                print "Installed image: "+self.bundleAll(fp.name, image)
                os.remove(fp.name)
            else:
                print "Image name not found, please run euca-describe-imagestore"

    def main_cli(self):
        self.cert_path = os.environ['EC2_CERT']
        self.private_key_path = os.environ['EC2_PRIVATE_KEY']
        self.user = os.environ['EC2_USER_ID']
        self.ec2cert_path = os.environ['EUCALYPTUS_CERT']
        self.debug=False
        self.do_cli()

