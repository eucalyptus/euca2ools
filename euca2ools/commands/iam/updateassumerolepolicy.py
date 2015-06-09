# Copyright 2014-2015 Eucalyptus Systems, Inc.
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

import json

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.argtypes import file_contents
from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_role


class UpdateAssumeRolePolicy(IAMRequest):
    DESCRIPTION = 'Update the policy that allows entities to assume a role'
    ARGS = [arg_role(help='role to update (required)'),
            MutuallyExclusiveArgList(
                Arg('-f', dest='PolicyDocument', metavar='FILE',
                    type=file_contents,
                    help='file containing the policy for the new role'),
                Arg('-s', '--service', route_to=None, help='''service to allow
                    access to the role (e.g. ec2.amazonaws.com)'''))
            .required(),
            Arg('-o', dest='verbose', action='store_true',
                help="also print the role's new policy"),
            AS_ACCOUNT]

    def preprocess(self):
        if self.args.get('service'):
            statement = {'Effect': 'Allow',
                         'Principal': {'Service': [self.args['service']]},
                         'Action': ['sts:AssumeRole']}
            policy = {'Version': '2008-10-17',
                      'Statement': [statement]}
            self.params['PolicyDocument'] = json.dumps(policy)

    def print_result(self, _):
        if self.args.get('verbose'):
            print self.params['PolicyDocument']
