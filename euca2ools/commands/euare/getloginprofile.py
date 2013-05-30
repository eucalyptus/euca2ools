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

from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from requestbuilder import Arg


class GetLoginProfile(EuareRequest):
    DESCRIPTION = 'Verify that a user has a password'
    ARGS = [Arg('-u', '--user-name', dest='UserName', metavar='USER',
                required=True, help='user whose password to verify (required)'),
            Arg('--verbose', action='store_true', route_to=None,
                help="print extra info about the user's password"),
            AS_ACCOUNT]

    def print_result(self, result):
        # If we've managed to get to this point, we already know the user has
        # a login profile.
        user_name = result['LoginProfile'].get('UserName')
        print 'Login Profile Exists for User', user_name
        if self.args['verbose']:
            create_date = result['LoginProfile'].get('CreateDate')
            if create_date:
                print 'Creation date:', create_date
            must_change = result['LoginProfile'].get('MustChangePassword')
            if must_change:
                print 'Must change password:', must_change
