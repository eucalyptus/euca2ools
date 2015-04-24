# Copyright 2015 Eucalyptus Systems, Inc.
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

from requestbuilder import Arg, MutuallyExclusiveArgList
from requestbuilder.command import BaseCommand

from euca2ools.commands import Euca2ools


class ReleaseRole(BaseCommand):
    DESCRIPTION = '''\
        Release IAM role credentials

        The %(prog)s utility removes the credentials created by
        euare-assumerole(1) by outputting shellcode that deletes
        the environment variables it creates.  Use it inside an eval
        command to make this process seamless:

            $ eval `euare-releaserole`

        Note that if the credentials used to initially assume the role
        were supplied in the form of environment variables those
        environment variables will need to be reset:

            $ source eucarc'''
    SUITE = Euca2ools
    ARGS = [MutuallyExclusiveArgList(
                Arg('-c', dest='csh_output', route_to=None,
                    action='store_true', help='''generate C-shell commands on
                    stdout (default if SHELL looks like a csh-style shell'''),
                Arg('-s', dest='sh_output', route_to=None,
                    action='store_true', help='''generate Bourne shell
                    commands on stdout (default if SHELL does not look
                    like a csh-style shell'''))]

    def print_result(self, _):
        for var in ('EC2_USER_ID', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_KEY',
                    'AWS_SECURITY_TOKEN', 'AWS_CREDENTIAL_EXPIRATION'):
            if (self.args.get('csh_output') or
                    (not self.args.get('sh_output') and
                     os.getenv('SHELL', '').endswith('csh'))):
                fmt = 'unsetenv {0};'
            else:
                fmt = 'unset {0};'
            print fmt.format(var)
