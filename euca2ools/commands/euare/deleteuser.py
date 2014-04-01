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

import argparse
from euca2ools.commands.euare import EuareRequest, AS_ACCOUNT
from euca2ools.commands.euare.deleteaccesskey import DeleteAccessKey
from euca2ools.commands.euare.deleteloginprofile import DeleteLoginProfile
from euca2ools.commands.euare.deletesigningcertificate import \
    DeleteSigningCertificate
from euca2ools.commands.euare.deleteuserpolicy import DeleteUserPolicy
from euca2ools.commands.euare.getloginprofile import GetLoginProfile
from euca2ools.commands.euare.listaccesskeys import ListAccessKeys
from euca2ools.commands.euare.listgroupsforuser import ListGroupsForUser
from euca2ools.commands.euare.listsigningcertificates import \
    ListSigningCertificates
from euca2ools.commands.euare.listuserpolicies import ListUserPolicies
from euca2ools.commands.euare.removeuserfromgroup import RemoveUserFromGroup
from euca2ools.exceptions import AWSError
from requestbuilder import Arg


class DeleteUser(EuareRequest):
    DESCRIPTION = 'Delete a user'
    ARGS = [Arg('-u', '--user-name', dest='UserName', metavar='USER',
                required=True, help='name of the user to delete (required)'),
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
            req = ListAccessKeys(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            keys = req.main().get('AccessKeyMetadata', [])
            req = ListUserPolicies(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            policies = req.main().get('PolicyNames', [])
            req = ListSigningCertificates(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            certs = req.main().get('Certificates', [])
            req = ListGroupsForUser(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            groups = req.main().get('Groups', [])
            req = GetLoginProfile(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
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
                    req = DeleteAccessKey(
                        config=self.config, service=self.service,
                        UserName=self.args['UserName'],
                        AccessKeyId=key['AccessKeyId'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for policy in policies:
                    req = DeleteUserPolicy(
                        config=self.config, service=self.service,
                        UserName=self.args['UserName'],
                        PolicyName=policy,
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for cert in certs:
                    req = DeleteSigningCertificate(
                        config=self.config, service=self.service,
                        UserName=self.args['UserName'],
                        CertificateId=cert['CertificateId'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                for group in groups:
                    req = RemoveUserFromGroup(
                        config=self.config, service=self.service,
                        user_names=[self.args['UserName']],
                        GroupName=group['GroupName'],
                        DelegateAccount=self.params['DelegateAccount'])
                    req.main()
                if has_login_profile:
                    req = DeleteLoginProfile(
                        config=self.config, service=self.service,
                        UserName=self.args['UserName'],
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
