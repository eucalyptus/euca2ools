# Copyright 2009-2015 Eucalyptus Systems, Inc.
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

import argparse

from requestbuilder import Arg

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_user
from euca2ools.commands.iam.deleteaccesskey import DeleteAccessKey
from euca2ools.commands.iam.deleteloginprofile import DeleteLoginProfile
from euca2ools.commands.iam.deletesigningcertificate import \
    DeleteSigningCertificate
from euca2ools.commands.iam.deleteuserpolicy import DeleteUserPolicy
from euca2ools.commands.iam.getloginprofile import GetLoginProfile
from euca2ools.commands.iam.listaccesskeys import ListAccessKeys
from euca2ools.commands.iam.listgroupsforuser import ListGroupsForUser
from euca2ools.commands.iam.listsigningcertificates import \
    ListSigningCertificates
from euca2ools.commands.iam.listuserpolicies import ListUserPolicies
from euca2ools.commands.iam.removeuserfromgroup import RemoveUserFromGroup
from euca2ools.exceptions import AWSError


class DeleteUser(IAMRequest):
    DESCRIPTION = 'Delete a user'
    ARGS = [arg_user(help='name of the user to delete (required)'),
            Arg('-r', '--recursive', action='store_true', route_to=None,
                help='''remove all IAM resources associated with the user
                        first'''),
            Arg('-R', '--recursive-euca', dest='IsRecursive',
                action='store_const', const='true', help=argparse.SUPPRESS),
            Arg('-p', '--pretend', action='store_true', route_to=None,
                help='''list the resources that would be deleted instead of
                        actually deleting them. Implies -r.'''),
            AS_ACCOUNT]

    def main(self):
        if self.args['recursive'] or self.args['pretend']:
            # Figure out what we'd have to delete
            req = ListAccessKeys.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            keys = req.main().get('AccessKeyMetadata', [])
            req = ListUserPolicies.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            policies = req.main().get('PolicyNames', [])
            req = ListSigningCertificates.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            certs = req.main().get('Certificates', [])
            req = ListGroupsForUser.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            groups = req.main().get('Groups', [])
            req = GetLoginProfile.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            try:
                # This will raise an exception if no login profile is found.
                req.main()
                has_login_profile = True
            except AWSError as err:
                if err.code == 'NoSuchEntity':
                    # It doesn't exist
                    has_login_profile = False
                else:
                    # Something else went wrong; not our problem
                    raise
        else:
            # Just in case
            keys = []
            policies = []
            certs = []
            groups = []
            has_login_profile = False
        if self.args['pretend']:
            return {'keys': keys, 'policies': policies,
                    'certificates': certs, 'groups': groups,
                    'has_login_profile': has_login_profile}
        else:
            if self.args['recursive']:
                for key in keys:
                    req = DeleteAccessKey.from_other(
                        self, UserName=self.args['UserName'],
                        AccessKeyId=key['AccessKeyId'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for policy in policies:
                    req = DeleteUserPolicy.from_other(
                        self, UserName=self.args['UserName'],
                        PolicyName=policy,
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for cert in certs:
                    req = DeleteSigningCertificate.from_other(
                        self, UserName=self.args['UserName'],
                        CertificateId=cert['CertificateId'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for group in groups:
                    req = RemoveUserFromGroup.from_other(
                        self, user_names=[self.args['UserName']],
                        GroupName=group['GroupName'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                if has_login_profile:
                    req = DeleteLoginProfile.from_other(
                        self, UserName=self.args['UserName'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
            return self.send()

    def print_result(self, result):
        if self.args['pretend']:
            print 'accesskeys'
            for key in result['keys']:
                print '\t' + key['AccessKeyId']
            print 'policies'
            for policy in result['policies']:
                print '\t' + policy
            print 'certificates'
            for cert in result['certificates']:
                print '\t' + cert['CertificateId']
            print 'groups'
            for group in result['groups']:
                print '\t' + group['Arn']
