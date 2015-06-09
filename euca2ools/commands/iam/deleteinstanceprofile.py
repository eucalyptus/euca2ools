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

from requestbuilder import Arg

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_iprofile
from euca2ools.commands.iam.deleterole import DeleteRole
from euca2ools.commands.iam.getinstanceprofile import GetInstanceProfile
from euca2ools.commands.iam.removerolefrominstanceprofile import \
    RemoveRoleFromInstanceProfile


class DeleteInstanceProfile(IAMRequest):
    DESCRIPTION = ('Delete an instance profile\n\nThis will break any running '
                   'instances that depend upon access to the deleted instance '
                   'profile.')
    ARGS = [arg_iprofile(
                help='name of the instance profile to delete (required)'),
            Arg('-r', '--recursive', action='store_true', route_to=None,
                help='''remove all IAM resources associated with the instance
                profile first'''),
            Arg('-p', '--pretend', action='store_true', route_to=None,
                help='''list the resources that would be deleted instead of
                actually deleting them.  Implies -r.'''),
            AS_ACCOUNT]

    def main(self):
        if self.args.get('recursive') or self.args.get('pretend'):
            # Figure out what we have to delete
            req = GetInstanceProfile.from_other(
                self, InstanceProfileName=self.args['InstanceProfileName'],
                DelegateAccount=self.args.get('DelegateAccount'))
            response = req.main()
            roles = []
            for role in response.get('InstanceProfile', {}).get('Roles') or []:
                roles.append({'arn': role.get('Arn'),
                              'name': role.get('RoleName')})
        else:
            # Just in case
            roles = []
        if self.args.get('pretend'):
            return {'roles': roles}
        else:
            if self.args.get('recursive'):
                for role in roles:
                    req = RemoveRoleFromInstanceProfile.from_other(
                        self, RoleName=role['name'],
                        InstanceProfileName=self.args['InstanceProfileName'],
                        DelegateAccount=self.args.get('DelegateAccount'))
                    req.main()
                    # This role could be attached to another instance
                    # profile, which means that a truly-recursive delete
                    # would need to also remove it from that instance
                    # profile, delete all of the role's policies, and
                    # so on.  The failure modes for this are rather nasty,
                    # so we don't tell DeleteRole to delete recursively;
                    # if the same role belongs to more than one instance
                    # profile then DeleteRole will simply fail harmlessly.
                    req = DeleteRole.from_other(
                        self, RoleName=role['name'],
                        DelegateAccount=self.args.get('DelegateAccount'))
                    req.main()
        return self.send()

    def print_result(self, result):
        if self.args.get('pretend'):
            print 'roles'
            for role in result['roles']:
                print '\t' + role['arn']
