# Copyright 2014-2015 Eucalyptus Systems, Inc.
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
from requestbuilder.auth.aws import QueryHmacV2Auth
from requestbuilder.mixins import FileTransferProgressBarMixin, TabifyingMixin

from euca2ools.commands.ec2 import EC2
from euca2ools.commands.ec2.registerimage import RegisterImage
from euca2ools.commands.empyrean import EmpyreanRequest
from euca2ools.commands.s3 import S3Request
from euca2ools.commands.bundle.bundleanduploadimage import BundleAndUploadImage
from euca2ools.commands.bundle.mixins import BundleCreatingMixin, \
    BundleUploadingMixin


class InstallImage(S3Request, BundleCreatingMixin, BundleUploadingMixin,
                   FileTransferProgressBarMixin, TabifyingMixin):
    DESCRIPTION = 'Bundle, upload and register an image into the cloud'
    ARGS = [Arg('-n', '--name', route_to=None, required=True,
                help='name of the new image (required)'),
            Arg('--description', route_to=None,
                help='description of the new image'),
            Arg('--max-pending-parts', type=int, default=2,
                help='''pause the bundling process when more than this number
                of parts are waiting to be uploaded (default: 2)'''),
            Arg('--virtualization-type', route_to=None,
                choices=('paravirtual', 'hvm'),
                help='virtualization type for the new image'),
            Arg('--platform', route_to=None, metavar='windows',
                choices=('windows',),
                help="[Privileged] the new image's platform (windows)"),
            Arg('--ec2-url', route_to=None,
                help='compute service endpoint URL'),
            Arg('--ec2-auth', route_to=None, help=argparse.SUPPRESS),
            Arg('--ec2-service', route_to=None, help=argparse.SUPPRESS)]

    def configure(self):
        # This goes before configure because -S's absence causes
        # self.auth.configure to blow up.  With an upload policy that
        # is undesirable.
        self.configure_bundle_upload_auth()

        S3Request.configure(self)

        if not self.args.get("ec2_service"):
            self.args["ec2_service"] = EC2.from_other(
                self.service, url=self.args.get('ec2_url'))
        if not self.args.get("ec2_auth"):
            self.args["ec2_auth"] = QueryHmacV2Auth.from_other(self.auth)

        if self.args.get('url') and not self.args.get('ec2_url'):
            self.log.warn('-U/--url used without --ec2-url; communication '
                          'with different regions may result')
        if self.args.get('ec2_url') and not self.args.get('url'):
            self.log.warn('--ec2-url used without -U/--url; communication '
                          'with different regions may result')

        # Set up access to empyrean in case we need auto cert fetching.
        try:
            self.args['empyrean_service'] = \
                EmpyreanRequest.SERVICE_CLASS.from_other(
                    self.service, url=self.args.get('empyrean_url'))
            self.args['empyrean_auth'] = EmpyreanRequest.AUTH_CLASS.from_other(
                self.auth)
        except:
            self.log.debug('empyrean setup failed; auto cert fetching '
                           'will be unavailable', exc_info=True)

        self.configure_bundle_creds()
        self.configure_bundle_properties()
        self.configure_bundle_output()

    def main(self):
        req = BundleAndUploadImage.from_other(
            self, image=self.args["image"], arch=self.args["arch"],
            bucket=self.args["bucket"], prefix=self.args.get("prefix"),
            destination=self.args.get("destination"),
            kernel=self.args.get("kernel"), ramdisk=self.args.get("ramdisk"),
            image_type=self.args.get("image_type"),
            image_size=self.args.get("image_size"), cert=self.args.get("cert"),
            privatekey=self.args.get("privatekey"),
            ec2cert=self.args.get("ec2cert"), user=self.args.get("user"),
            productcodes=self.args.get("productcodes"),
            enc_iv=self.args.get("enc_iv"), enc_key=self.args.get("enc_key"),
            max_pending_parts=self.args.get("max_pending_parts"),
            part_size=self.args.get("part_size"), batch=self.args.get("batch"),
            show_progress=self.args.get("show_progress"),
            show_porcelain=self.args.get('show_porcelain'))
        result_bundle = req.main()
        image_location = result_bundle['manifests'][0]["key"]

        req = RegisterImage.from_other(
            self, service=self.args["ec2_service"], auth=self.args["ec2_auth"],
            Name=self.args["name"], Architecture=self.args["arch"],
            ImageLocation=image_location,
            Description=self.args.get("description"),
            VirtualizationType=self.args.get("virtualization_type"),
            Platform=self.args.get("platform"))
        result_register = req.main()
        return result_register

    def print_result(self, result):
        print self.tabify(('IMAGE', result.get('imageId')))
