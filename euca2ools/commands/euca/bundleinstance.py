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

import base64
from datetime import datetime, timedelta
from euca2ools.commands.euca import EucalyptusRequest
import hashlib
import hmac
import json
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError


class BundleInstance(EucalyptusRequest):
    DESCRIPTION = 'Bundle an S3-backed Windows instance'
    ARGS = [Arg('InstanceId', metavar='INSTANCE',
                help='ID of the instance to bundle (required)'),
            Arg('-b', '--bucket', dest='Storage.S3.Bucket', metavar='BUCKET',
                required=True, help='''bucket in which to store the new machine
                image (required)'''),
            Arg('-p', '--prefix', dest='Storage.S3.Prefix', metavar='PREFIX',
                required=True,
                help='beginning of the machine image bundle name (required)'),
            Arg('-o', '--owner-akid', '--user-access-key', metavar='KEY-ID',
                dest='Storage.S3.AWSAccessKeyId', required=True,
                help="bucket owner's access key ID (required)"),
            Arg('-c', '--policy', metavar='POLICY',
                dest='Storage.S3.UploadPolicy',
                help='''Base64-encoded upload policy that allows the server
                        to upload a bundle on your behalf.  If unused, -w is
                        required.'''),
            Arg('-s', '--policy-signature', metavar='SIGNATURE',
                dest='Storage.S3.UploadPolicySignature',
                help='''signature of the Base64-encoded upload policy.  If
                        unused, -w is required.'''),
            Arg('-w', '--owner-sak', '--user-secret-key', metavar='KEY',
                route_to=None,
                help="""bucket owner's secret access key, used to sign upload
                        policies.  This is required unless both -c and -s are
                        used."""),
            Arg('-x', '--expires', metavar='HOURS', type=int, default=24,
                route_to=None,
                help='generated upload policy expiration time (default: 24)')]

    def generate_default_policy(self):
        delta = timedelta(hours=self.args['expires'])
        expire_time = (datetime.utcnow() + delta).replace(microsecond=0)

        policy = {'conditions': [{'acl':    'ec2-bundle-read'},
                                 {'bucket': self.args.get('Storage.S3.Bucket')},
                                 ['starts-with', '$key',
                                  self.args.get('Storage.S3.Prefix')]],
                  'expiration': expire_time.isoformat()}
        policy_json = json.dumps(policy)
        self.log.info('generated default policy: %s', policy_json)
        self.params['Storage.S3.UploadPolicy'] = base64.b64encode(policy_json)

    def sign_policy(self):
        my_hmac = hmac.new(self.args['owner_sak'], digestmod=hashlib.sha1)
        my_hmac.update(self.params.get('Storage.S3.UploadPolicy'))
        self.params['Storage.S3.UploadPolicySignature'] = \
            base64.b64encode(my_hmac.digest())

    # noinspection PyExceptionInherit
    def configure(self):
        EucalyptusRequest.configure(self)
        if not self.args.get('Storage.S3.UploadPolicy'):
            if not self.args.get('owner_sak'):
                raise ArgumentError('argument -w/--owner-sak is required when '
                                    '-c/--policy is not used')
        elif not self.args.get('Storage.S3.UploadPolicySignature'):
            if not self.args.get('owner_sak'):
                raise ArgumentError('argument -w/--owner-sak is required when '
                                    '-s/--policy-signature is not used')

    def preprocess(self):
        if not self.args.get('Storage.S3.UploadPolicy'):
            self.generate_default_policy()
        if not self.args.get('Storage.S3.UploadPolicySignature'):
            self.sign_policy()

    def print_result(self, result):
        self.print_bundle_task(result['bundleInstanceTask'])
