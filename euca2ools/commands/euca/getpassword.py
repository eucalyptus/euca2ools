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
from euca2ools.commands.euca.getpassworddata import GetPasswordData
from requestbuilder import Arg
import subprocess


class GetPassword(GetPasswordData):
    NAME = 'GetPasswordData'
    DESCRIPTION = ('Retrieve the administrator password for an instance '
                   'running Windows')
    ARGS = [Arg('-k', '--priv-launch-key', metavar='FILE', required=True,
                route_to=None,
                help='''file containing the private key corresponding to the
                key pair supplied at instance launch time (required)''')]

    def print_result(self, result):
        try:
            pwdata = result['passwordData']
        except AttributeError:
            # The reply didn't contain a passwordData element.
            raise AttributeError('no password data found for this instance')
        cmd = subprocess.Popen(['openssl', 'rsautl', '-decrypt', '-inkey',
                                self.args['priv_launch_key']],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, __ = cmd.communicate(base64.b64decode(pwdata))
        print stdout
