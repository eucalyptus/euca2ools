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

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_server_cert


class UploadServerCertificate(IAMRequest):
    DESCRIPTION = 'Upload a server certificate'
    ARGS = [arg_server_cert(
                help='name to give the new server certificate (required)'),
            MutuallyExclusiveArgList(
                Arg('-c', '--certificate-body', dest='CertificateBody',
                    metavar='CERT_CONTENT', help='PEM-encoded certificate'),
                Arg('--certificate-file', dest='CertificateBody',
                    metavar='FILE', type=open,
                    help='file containing the PEM-encoded certificate'))
            .required(),
            MutuallyExclusiveArgList(
                Arg('--private-key', dest='PrivateKey', metavar='KEY',
                    help='PEM-encoded private key'),
                Arg('--private-key-file', dest='PrivateKey', metavar='FILE',
                    type=open,
                    help='file containing the PEM-encoded private key'))
            .required(),
            MutuallyExclusiveArgList(
                Arg('--certificate-chain', dest='CertificateChain',
                    metavar='CHAIN', help='''PEM-encoded certificate chain.
                    This is typically the PEM-encoded certificates of the
                    chain, concatenated together.'''),
                Arg('--certificate-chain-file', dest='CertificateChain',
                    metavar='FILE', type=open,
                    help='''file containing the PEM-encoded
                    certificate chain. This is typically the PEM-encoded
                    certificates of the chain, concatenated together.''')),
            Arg('-p', '--path', dest='Path',
                help='path for the new server certificate (default: "/")'),
            AS_ACCOUNT]
