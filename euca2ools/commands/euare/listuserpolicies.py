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

from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from euca2ools.commands.euare.getuserpolicy import GetUserPolicy
from requestbuilder import Arg
from requestbuilder.response import PaginatedResponse


class ListUserPolicies(EuareRequest):
    DESCRIPTION = ('List one specific policy or all policies attached to a '
                   'user.  If no policies are attached to the user, the '
                   'action still succeeds.')
    ARGS = [Arg('-u', '--user-name', dest='UserName', metavar='USER',
                required=True, help='user owning the policies to list'),
            Arg('-p', '--policy-name', metavar='POLICY', route_to=None,
                help='display a specific policy'),
            Arg('-v', '--verbose', action='store_true', route_to=None,
                help='''display the contents of the resulting policies (in
                        addition to their names)'''),
            Arg('--pretty-print', action='store_true', route_to=None,
                help='''when printing the contents of policies, reformat them
                        for easier reading'''),
            AS_ACCOUNT]
    LIST_TAGS = ['PolicyNames']

    def main(self):
        return PaginatedResponse(self, (None,), ('PolicyNames',))

    def prepare_for_page(self, page):
        # Pages are defined by markers
        self.params['Marker'] = page

    def get_next_page(self, response):
        if response.get('IsTruncated') == 'true':
            return response['Marker']

    def print_result(self, result):
        if self.args.get('policy_name'):
            # Look for the specific policy the user asked for
            for policy_name in result.get('PolicyNames', []):
                if policy_name == self.args['policy_name']:
                    if self.args['verbose']:
                        self.print_policy(policy_name)
                    else:
                        print policy_name
                    break
        else:
            for policy_name in result.get('PolicyNames', []):
                print policy_name
                if self.args['verbose']:
                    self.print_policy(policy_name)

    def print_policy(self, policy_name):
        req = GetUserPolicy(service=self.service,
            UserName=self.args['UserName'], PolicyName=policy_name,
            pretty_print=self.args['pretty_print'],
            DelegateAccount=self.args.get('DelegateAccount'))
        response = req.main()
        req.print_result(response)
