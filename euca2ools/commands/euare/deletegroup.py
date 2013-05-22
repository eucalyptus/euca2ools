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

import argparse
from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from euca2ools.commands.euare.deletegrouppolicy import DeleteGroupPolicy
from euca2ools.commands.euare.getgroup import GetGroup
from euca2ools.commands.euare.listgrouppolicies import ListGroupPolicies
from euca2ools.commands.euare.removeuserfromgroup import RemoveUserFromGroup
from requestbuilder import Arg


class DeleteGroup(EuareRequest):
    DESCRIPTION = 'Delete a group'
    ARGS = [Arg('-g', '--group-name', dest='GroupName', metavar='GROUP',
                required=True, help='name of the group to delete (required)'),
            Arg('-r', '--recursive', action='store_true', route_to=None,
                help='''remove all user memberships and policies associated
                        with the group first'''),
            Arg('-R', '--recursive-euca', dest='IsRecursive',
                action='store_const', const='true', help=argparse.SUPPRESS),
            Arg('-p', '--pretend', action='store_true', route_to=None,
                help='''list the user memberships and policies that would be
                deleted instead of actually deleting them. Implies -r.'''),
            AS_ACCOUNT]

    def main(self):
        if self.args['recursive'] or self.args['pretend']:
            # Figure out what we'd have to delete
            req = GetGroup(config=self.config, service=self.service,
                           GroupName=self.args['GroupName'],
                           DelegateAccount=self.params['DelegateAccount'])
            members = req.main().get('Users', [])
            req = ListGroupPolicies(
                config=self.config, service=self.service,
                GroupName=self.args['GroupName'],
                DelegateAccount=self.params['DelegateAccount'])
            policies = req.main().get('PolicyNames', [])
        if self.args['pretend']:
            return {'members':  [member['Arn'] for member in members],
                    'policies': policies}
        else:
            if self.args['recursive']:
                member_names = [member['UserName'] for member in members]
                req = RemoveUserFromGroup(
                    config=self.config, service=self.service,
                    GroupName=self.args['GroupName'],
                    user_names=member_names,
                    DelegateAccount=self.params['DelegateAccount'])
                req.main()
                for policy in policies:
                    req = DeleteGroupPolicy(
                        config=self.config, service=self.service,
                        GroupName=self.args['GroupName'], PolicyName=policy,
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
            return self.send()

    def print_result(self, result):
        if self.args['pretend']:
            print 'users'
            for arn in result['members']:
                print '\t' + arn
            print 'policies'
            for policy in result['policies']:
                print '\t' + policy
