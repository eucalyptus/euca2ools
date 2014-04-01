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

import json

from requestbuilder import Arg

from euca2ools.commands.iam import EuareRequest, AS_ACCOUNT
from euca2ools.commands.iam.putrolepolicy import PutRolePolicy
from euca2ools.util import build_iam_policy


class AddRolePolicy(EuareRequest):
    DESCRIPTION = ('Add a new policy to a role.  To add more complex policies '
                   'than this tool supports, see euare-roleuploadpolicy.')
    ARGS = [Arg('-r', '--role-name', metavar='ROLE', required=True,
                help='role to attach the policy to (required)'),
            Arg('-p', '--policy-name', metavar='POLICY', required=True,
                help='name of the new policy (required)'),
            Arg('-e', '--effect', choices=('Allow', 'Deny'), required=True,
                help='whether the new policy should Allow or Deny (required)'),
            Arg('-a', '--action', dest='actions', action='append',
                required=True, help='''action(s) the policy should apply to
                (at least one required)'''),
            Arg('-c', '--resource', dest='resources', action='append',
                required=True, help='''resource(s) the policy should apply to
                (at least one required)'''),
            Arg('-o', '--output', action='store_true',
                help='also display the newly-created policy'),
            AS_ACCOUNT]

    def main(self):
        policy = build_iam_policy(self.args['effect'], self.args['resources'],
                                  self.args['actions'])
        policy_doc = json.dumps(policy)
        req = PutRolePolicy(
            config=self.config, service=self.service,
            RoleName=self.args['role_name'],
            PolicyName=self.args['policy_name'],
            PolicyDocument=policy_doc,
            DelegateAccount=self.params['DelegateAccount'])
        response = req.main()
        response['PolicyDocument'] = policy_doc
        return response

    def print_result(self, result):
        if self.args['output']:
            print result['PolicyDocument']
