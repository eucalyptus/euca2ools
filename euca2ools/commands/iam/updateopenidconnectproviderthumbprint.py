# Copyright (c) 2016 Hewlett Packard Enterprise Development LP
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

from requestbuilder import Arg
from requestbuilder.exceptions import ClientError

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, util
from euca2ools.commands.iam.getopenidconnectprovider import \
    GetOpenIDConnectProvider


class UpdateOpenIDConnectProviderThumbprint(IAMRequest):
    """
    Replace an OpenID Connect provider's list of thumbprints
    """

    ARGS = [Arg('OpenIDConnectProviderArn', metavar='OIDC',
                help='the ARN of the provider to update (required)'),
            Arg('-t', '--thumbprint', dest='ThumbprintList.member',
                metavar='HEX', action='append', help='''the new SHA-1
                thumbprint of the OpenID Connect provider's certificate.  This
                option may be specified more than once to allow multiple
                certificates to be accepted.  If one is not supplied this
                command will attempt to determine it automatically.'''),
            AS_ACCOUNT]

    def preprocess(self):
        if not self.args.get('ThumbprintList.member'):
            req = GetOpenIDConnectProvider.from_other(
                self, OpenIDConnectProviderArn=self.args.get(
                    'OpenIDConnectProviderArn'))
            url = req.main().get('Url')
            if not url:
                raise ClientError("unable to determine the provider's URL "
                                  "automatically; please specify a thumbprint "
                                  "with -t/--thumbprint")
            elif '://' not in url:
                # URLs seem to come back from IAM without schemes
                url = 'https://{0}'.format(url)
            self.params['ThumbprintList.member.1'] = \
                util.get_cert_fingerprint(url, log=self.log)
