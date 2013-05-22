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

import datetime
from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from euca2ools.commands.euare.putgrouppolicy import PutGroupPolicy
import json
from requestbuilder import Arg


class AddGroupPolicy(EuareRequest):
    DESCRIPTION = ('Add a new policy to a group. To add more complex policies '
                   'than this tool supports, see euare-groupuploadpolicy.')
    ARGS = [Arg('-g', '--group-name', metavar='GROUP', required=True,
                help='group to attach the policy to (required)'),
            Arg('-p', '--policy-name', metavar='POLICY', required=True,
                help='name of the new policy (required)'),
            Arg('-e', '--effect', choices=('Allow', 'Deny'), required=True,
                help='whether the new policy should Allow or Deny (required)'),
            Arg('-a', '--action', required=True,
                help='action the policy should apply to (required)'),
            Arg('-r', '--resource', required=True,
                help='resource the policy should apply to (required)'),
            Arg('-o', '--output', action='store_true',
                help='display the newly-created policy'),
            AS_ACCOUNT]

    def build_policy(self):
        stmt = {'Sid': datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f'),
                'Effect':   self.args['effect'],
                'Action':   self.args['action'],
                'Resource': self.args['resource']}
        return {'Statement': [stmt]}

    def main(self):
        policy_doc = json.dumps(self.build_policy())
        req = PutGroupPolicy(
            config=self.config, service=self.service,
            GroupName=self.args['group_name'],
            PolicyName=self.args['policy_name'],
            PolicyDocument=policy_doc,
            DelegateAccount=self.params['DelegateAccount'])
        response = req.main()
        response['PolicyDocument'] = policy_doc
        return response

    def print_result(self, result):
        if self.args['output']:
            print result['PolicyDocument']
