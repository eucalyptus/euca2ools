#!/usr/bin/env python
#
# Software License Agreement (BSD License)
#
# Copyright (c) 2014, Eucalyptus Systems, Inc.
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
import os
import subprocess
import sys

import euca2ools
(major, minor, patch) = euca2ools.__version__.split('-')[0].split('.')
if int(major) < 3 or (int(major) >= 3 and int(minor) < 1):
    print >> sys.stderr, "euca2ools version 3.1.0 or newer required."
    sys.exit(1)


class InstallImage(object):
    @staticmethod
    def _get_env():
        return os.environ.copy()

    def _check_dependency(self, path):
        env = self._get_env()
        cmd = [path]
        try:
            with open(os.devnull, 'w') as nullfile:
                subprocess.call(cmd, env=env, stdout=nullfile, stderr=nullfile)
        except OSError:
            print >> sys.stderr, "Error cannot find: " + path
            sys.exit(1)

    def _check_creds(self):
        var_list = ["EC2_URL", "S3_URL"]
        for var in var_list:
            if not var in self._get_env():
                print "Error: " + var + " environment variable not set."
                sys.exit(1)

    def install_image(self, image_file, bucket, name, virtualization_type,
                      architecture):
        ### Bundle and upload image
        self._check_dependency("euca-bundle-and-upload-image")
        self._check_dependency("euca-register")
        install_cmd = "euca-bundle-and-upload-image " \
                      "-b {0} -i {1} -r {2}".format(bucket, image_file,
                                                    architecture)
        print "Bundling and uploading image to bucket: " + bucket
        bundle_output = subprocess.Popen(install_cmd, env=self._get_env(),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         shell=True)
        bundle_output.wait()
        bundle_stdout = bundle_output.stdout.read()
        bundle_stderr = bundle_output.stderr.read()
        if bundle_output.returncode > 0:
            print "Error: Unable to bundle and upload image.\n" \
                  + bundle_stdout + bundle_stderr
            sys.exit(1)

        try:
            manifest = bundle_stdout.split()[1]
        except IndexError:
            print "Error: Unable to retrieve uploaded image manifest."
            sys.exit(1)

        register_cmd = "euca-register {0} --name {1} " \
                       "--virtualization-type {2}".format(manifest,
                                                          name,
                                                          virtualization_type)
        print "Registering image manifest: " + manifest
        register_output = subprocess.Popen(register_cmd, env=self._get_env(),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True)
        register_output.wait()
        register_stdout = register_output.stdout.read()
        register_stderr = register_output.stderr.read()
        if register_output.returncode > 0:
            print "Error: Unable to register image.\n" + \
                  register_stdout + register_stderr
            sys.exit(1)
        emi_id = register_stdout.split()[1]
        print "Registered image: " + emi_id

    @staticmethod
    def run():
        description = '''
        Image Installation Tool:

        This tool provides an easy way to install a Eucalyptus Image.
        Images can be downloaded from:
        http://emis.eucalyptus.com/
        '''
        parser = argparse.ArgumentParser(formatter_class=
                                         argparse.RawDescriptionHelpFormatter,
                                         description=description)
        parser.add_argument('-v', '--virtualization-type',
                            metavar='{paravirtual,hvm}',
                            help='Virtualization type of the image '
                                 'to be registered. '
                                 'Possible options are: hvm, paravirtual',
                            default="hvm")
        parser.add_argument('-i', '--image', metavar='IMAGE', required=True,
                            help='Image file to upload, bundle, and register')

        parser.add_argument("-b", "--bucket", metavar='BUCKET', required=True,
                            help='Bucket to upload image to')
        parser.add_argument("-n", "--name", metavar='NAME', required=True,
                            help='Name of image to register')
        parser.add_argument("-a", "--architecture",
                            metavar='{i386,x86_64,armhf}', required=True,
                            help='CPU architecture of the new image')

        args = parser.parse_args()
        install_tool = InstallImage()
        install_tool.install_image(args.image, args.bucket,
                                   args.name, args.virtualization_type,
                                   args.architecture)
