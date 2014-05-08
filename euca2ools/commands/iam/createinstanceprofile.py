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

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT
from euca2ools.commands.iam.addroletoinstanceprofile import \
    AddRoleToInstanceProfile
from euca2ools.commands.iam.createrole import CreateRole


class CreateInstanceProfile(IAMRequest):
    DESCRIPTION = 'Create a new instance profile'
    ARGS = [Arg('-s', '--instance-profile-name', dest='InstanceProfileName',
                metavar='IPROFILE', required=True,
                help='name of the new instance profile (required)'),
            Arg('-p', '--path', dest='Path',
                help='path for the new instance profile (default: "/")'),
            MutuallyExclusiveArgList(
                Arg('-r', '--add-role', dest='role', route_to=None,
                    help='also add a role to the new instance profile'),
                Arg('--create-role', dest='create_role', route_to=None,
                    action='store_true', help='''also create a role with the
                    same name and path and add it to the instance profile''')),
            Arg('-v', '--verbose', action='store_true', route_to=None,
                help="print the new instance profile's ARN and GUID"),
            AS_ACCOUNT]

    def postprocess(self, _):
        role_name = None
        if self.args.get('create_role'):
            role_name = self.args['InstanceProfileName']
            req = CreateRole.from_other(
                self, RoleName=role_name, Path=self.args.get('path'),
                service_='ec2.amazonaws.com',
                DelegateAccount=self.args.get('DelegateAccount'))
            req.main()
        elif self.args.get('role'):
            role_name = self.args['role']

        if role_name:
            self.log.info('adding role %s to instance profile %s',
                          self.args['role'], self.args['InstanceProfileName'])
            req = AddRoleToInstanceProfile.from_other(
                self, RoleName=role_name,
                InstanceProfileName=self.args['InstanceProfileName'],
                DelegateAccount=self.args.get('DelegateAccount'))
            req.main()

    def print_result(self, result):
        if self.args.get('verbose'):
            print result.get('InstanceProfile', {}).get('Arn')
            print result.get('InstanceProfile', {}).get('InstanceProfileId')
