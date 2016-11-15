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
from requestbuilder.exceptions import ArgumentError
import six.moves.urllib.parse

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, util


class CreateOpenIDConnectProvider(IAMRequest):
    """
    Create a new OpenID Connect provider
    """

    ARGS = [Arg('Url', metavar='URL',
                help='the URL for the new provider (required)'),
            Arg('-c', '--client-id', dest='ClientIdList.member',
                metavar='CLIENT', action='append',
                help='a client ID, or audience, for the new provider'),
            Arg('-t', '--thumbprint', dest='ThumbprintList.member',
                metavar='HEX', action='append', help='''the SHA-1 thumbprint
                of the new OpenID Connect provider's certificate.  If one is
                not supplied this command will attempt to connect to the
                server to determine it automatically.'''),
            AS_ACCOUNT]

    def configure(self):
        IAMRequest.configure(self)
        parsed = six.moves.urllib.parse.urlparse(self.args.get('Url') or '')
        if parsed.scheme != 'https':
            raise ArgumentError('URL must begin with "https://"')
        if not parsed.netloc:
            raise ArgumentError('URL must name a host to connect to')

    def preprocess(self):
        if not self.args.get('ThumbprintList.member'):
            self.params['ThumbprintList.member.1'] = \
                util.get_cert_fingerprint(self.args['Url'], log=self.log)

    # pylint: disable=no-self-use
    def print_result(self, result):
        print result.get('OpenIDConnectProviderArn')
    # pylint: enable=no-self-use
