# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

import argparse
from euca2ools.commands.bundle import add_bundle_creds
from euca2ools.commands.bundle.bundleimage import BundleImage
from euca2ools.commands.bundle.uploadbundle import UploadBundle
from euca2ools.nc.auth import EucaRsaV2Auth
from euca2ools.nc.services import NCInternalWalrus
from requestbuilder import Arg
import requestbuilder.command


# FIXME:  This should actually use the policy given by the user instead of
#         EucaRsaV2Auth.  It previously attempted to use both at the same time,
#         leading to amusing code paths in walrus, so for the moment it uses
#         the latter exclusively.


class BundleAndUpload(requestbuilder.command.BaseCommand):
    DESCRIPTION = ('[Eucalyptus NC internal] Bundle and upload an image on '
                   'behalf of a user')
    ARGS = [Arg('-b', '--bucket', required=True,
                help='bucket to upload the bundle to (required)'),
            Arg('-i', '--image', required=True,
                help='file containing the image to bundle (required)'),
            # --arch's default should go away when these bugs are fixed:
            # https://eucalyptus.atlassian.net/browse/EUCA-5979
            # https://eucalyptus.atlassian.net/browse/EUCA-5980
            Arg('-r', '--arch', default='x86_64',
                help='image architecture (default: x86_64)'),
            Arg('-d', '--directory', help='''location to place the working
                directory with temporary files'''),
            Arg('--cert', metavar='FILE',
                help='''file containing the X.509 certificate to use when
                signing requests and bundling the image'''),
            Arg('--privatekey', metavar='FILE',
                help='''file containing the private key to use when signing
                requests and bundling the image'''),
            Arg('--spoof-key-id', metavar='KEY_ID',
                help='run this command as if signed by a specific access key'),
            Arg('--ec2cert', metavar='FILE',
                help="file containing the cloud's X.509 certificate"),
            Arg('--user', metavar='ACCOUNT', help="the user's account ID"),
            Arg('-c', '--upload-policy', metavar='POLICY',
                help='Base64-encoded S3 upload policy'),
            Arg('--upload-policy-signature', '--policysignature',
                dest='upload_policy_signature', metavar='SIGNATURE',
                route_to=None, help='''signature for the upload policy given
                with --upload-policy'''),
            Arg('-U', '--url', help='storage service endpoint URL'),
            Arg('--euca-auth', action='store_true', help=argparse.SUPPRESS),
            Arg('--kernel', metavar='IMAGE', help='''ID of the kernel image to
                associate with the machine bundle'''),
            Arg('--ramdisk', metavar='IMAGE', help='''ID of the ramdisk image
                to associate with the machine bundle''')]
    # Note that this is a back end service for which region support is
    # out of scope.  This isn't going to get tested with that.

    def configure(self):
        requestbuilder.command.BaseCommand.configure(self)

        add_bundle_creds(self.args, self.config)

        walrus_auth = EucaRsaV2Auth(
            config=self.config, loglevel=self.log.level,
            cert=self.args.get('cert'), privatekey=self.args.get('privatekey'),
            spoof_key_id=self.args.get('spoof_key_id'))
        self.__walrus = NCInternalWalrus(auth=walrus_auth, config=self.config,
                                         loglevel=self.log.level,
                                         url=self.args.get('url'))
        self.__walrus.configure()


    def main(self):
        cmd = BundleImage(image=self.args['image'], arch=self.args['arch'],
                          cert=self.args['cert'],
                          privatekey=self.args['privatekey'],
                          user=self.args['user'],
                          destination=self.args.get('directory'),
                          ec2cert=self.args['ec2cert'], image_type='machine',
                          config=self.config,
                          kernel=self.args['kernel'],
                          ramdisk=self.args['ramdisk'])
        parts, manifest = cmd.main()

        cmd = UploadBundle(bucket=self.args['bucket'], manifest=manifest,
                           acl='ec2-bundle-read', config=self.config,
                           service=self.__walrus)
        manifest_loc = cmd.main()
        return manifest_loc
