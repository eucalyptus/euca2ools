# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2013, Eucalyptus Systems, Inc.
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

import base64
from M2Crypto import RSA
from requestbuilder import Arg
from .argtypes import file_contents
from .getpassworddata import GetPasswordData

class GetPassword(GetPasswordData):
    ACTION = 'GetPasswordData'
    DESCRIPTION = '''Retrieve the administrator password for an instance
                     running Windows'''
    ARGS = [Arg('-k', '--priv-launch-key', metavar='PRIVKEY',
                type=file_contents, required=True, route_to=None,
                help='''file containing the private key corresponding to the
                        key pair supplied at instance launch time''')]

    def print_result(self, result):
        try:
            pwdata = result['passwordData']
        except AttributeError:
            # The reply didn't contain a passwordData element.
            raise AttributeError('no password data found for this instance')
        privkey  = RSA.load_key_string(self.args['priv_launch_key'])
        password = privkey.private_decrypt(base64.b64decode(pwdata),
                                           RSA.pkcs1_padding)
        print password
