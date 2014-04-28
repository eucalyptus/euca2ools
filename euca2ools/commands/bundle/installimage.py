# Copyright 2014 Eucalyptus Systems, Inc.
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

from __future__ import division

import argparse

from requestbuilder import Arg
from requestbuilder.auth import QuerySigV2Auth
from requestbuilder.mixins import FileTransferProgressBarMixin, TabifyingMixin
from euca2ools.commands.bundle.mixins import BundleCreatingMixin, \
    BundleUploadingMixin


from euca2ools.commands.ec2 import EC2
from euca2ools.commands.ec2.registerimage import RegisterImage
from euca2ools.commands.s3 import S3Request
from euca2ools.commands.bundle.bundleanduploadimage import BundleAndUploadImage


class InstallImage(S3Request, BundleCreatingMixin, BundleUploadingMixin,
                   FileTransferProgressBarMixin, TabifyingMixin):
    DESCRIPTION = 'Bundle, upload and register an image into the cloud'
    ARGS = [Arg('-n', '--name', route_to=None, help="Name of registered image",
                required=True),
            Arg('-v', '--virtualization-type', route_to=None,
                help="Virtualziation type of image", required=True),
            Arg('--description', route_to=None, help="Description of image"),
            Arg('--max-pending-parts', type=int, default=2,
                help='''pause the bundling process when more than this number
                of parts are waiting to be uploaded (default: 2)'''),
            Arg('--platform', route_to=None, metavar='windows',
                choices=('windows',),
                help="[Privileged] the new image's platform (windows)"),
            Arg('--ec2-url', route_to=None,
                help="EC2 Endpoint to use for registering image"),
            Arg('--ec2-auth', route_to=None, help=argparse.SUPPRESS),
            Arg('--ec2-service', route_to=None, help=argparse.SUPPRESS)]

    def configure(self):
        S3Request.configure(self)
        self.configure_bundle_upload_auth()
        self.configure_bundle_creds()
        self.configure_bundle_output()
        self.configure_bundle_properties()

        if not self.args.get("ec2_service"):
            self.args["ec2_service"] = EC2.from_other(
                self.service, url=self.args.get('ec2_url'))

        if not self.args.get("ec2_auth"):
            self.args["ec2_auth"] = QuerySigV2Auth.from_other(self.auth)

    def main(self):
        print "Bundling and uploading: " + self.args["image"].name
        req = BundleAndUploadImage.from_other(
            self, bucket=self.args["bucket"], image=self.args["image"],
            arch=self.args["arch"], destination=self.args["destination"],
            image_type=self.args["image_type"], prefix=self.args["prefix"],
            image_size=self.args["image_size"], cert=self.args["cert"],
            privatekey=self.args["privatekey"], ec2cert=self.args["ec2cert"],
            user=self.args["user"], productcodes=self.args["productcodes"],
            enc_iv=self.args["enc_iv"], enc_key=self.args["enc_key"],
            max_pending_parts=self.args["max_pending_parts"],
            part_size=self.args["part_size"], batch=self.args["batch"],
            show_progress=self.args["show_progress"])
        result_bundle = req.main()
        image_location = result_bundle['manifests'][0]["key"]

        print "Registering manifest: " + image_location
        req = RegisterImage.from_other(
            self, service=self.args["ec2_service"], Name=self.args["name"],
            auth=self.args["ec2_auth"], Architecture=self.args["arch"],
            ImageLocation=image_location, Description=self.args["description"],
            VirtualizationType=self.args["virtualization_type"],
            KernelId=self.args["kernel"], RamdiskId=self.args["ramdisk"],
            Platform=self.args["platform"])
        result_register = req.main()
        return result_register

    def print_result(self, result):
        print "Registered image: " + result['imageId']
