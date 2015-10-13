# Copyright 2009-2015 Eucalyptus Systems, Inc.
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

import os

from requestbuilder import Arg

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_user


class CreateSigningCertificate(IAMRequest):
    DESCRIPTION = '[Eucalyptus only] Create a new signing certificate'
    ARGS = [arg_user(nargs='?', help='''user to create the signing
                     certificate for (default: current user)'''),
            Arg('--out', metavar='FILE', route_to=None,
                help='file to write the certificate to (default: stdout)'),
            Arg('--keyout', metavar='FILE', route_to=None,
                help='file to write the private key to (default: stdout)'),
            AS_ACCOUNT]

    def postprocess(self, result):
        if self.args['out']:
            with open(self.args['out'], 'w') as certfile:
                certfile.write(result['Certificate']['CertificateBody'])
        if self.args['keyout']:
            old_umask = os.umask(0o077)
            with open(self.args['keyout'], 'w') as keyfile:
                keyfile.write(result['Certificate']['PrivateKey'])
            os.umask(old_umask)

    def print_result(self, result):
        print result['Certificate']['CertificateId']
        if not self.args['out']:
            print result['Certificate']['CertificateBody']
        if not self.args['keyout']:
            print result['Certificate']['PrivateKey']
