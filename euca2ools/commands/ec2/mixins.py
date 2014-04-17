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

import argparse

from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError

from euca2ools.commands.s3 import S3, S3Request


class S3AccessMixin(object):
    ARGS = [Arg('--s3-url', metavar='URL', route_to=None,
                help='object storage service endpoint URL'),
            Arg('-o', '--owner-akid', metavar='KEY_ID', route_to=None,
                help='''access key to use for the object storage service
                (default: same as that for the compute service)'''),
            Arg('-w', '--owner-sak', metavar='KEY', route_to=None,
                help='''secret key to use for the object storage service
                (default: same as that for the compute service)'''),
            # Pass-throughs
            Arg('--s3-service', route_to=None, help=argparse.SUPPRESS),
            Arg('--s3-auth', route_to=None, help=argparse.SUPPRESS)]

    def configure_s3_access(self):
        if self.args.get('owner_akid') and not self.args.get('owner_sak'):
            raise ArgumentError('argument -o/--owner-akid also requires '
                                '-w/--owner-sak')
        if self.args.get('owner_sak') and not self.args.get('owner_akid'):
            raise ArgumentError('argument -w/--owner-sak also requires '
                                '-o/--owner-akid')
        if not self.args.get('s3_auth'):
            if self.args.get('owner_sak') and self.args.get('owner_akid'):
                self.args['s3_auth'] = S3Request.AUTH_CLASS.from_other(
                    self.auth, key_id=self.args['owner_akid'],
                    secret_key=self.args['owner_sak'])
            else:
                self.args['s3_auth'] = S3Request.AUTH_CLASS.from_other(
                    self.auth)
        if not self.args.get('s3_service'):
            self.args['s3_service'] = S3.from_other(self.service)
