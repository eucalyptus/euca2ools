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

import sys

from requestbuilder import Arg, MutuallyExclusiveArgList

from euca2ools.commands.iam import IAMRequest, AS_ACCOUNT, arg_user
from euca2ools.commands.iam.addusertogroup import AddUserToGroup
from euca2ools.commands.iam.createaccesskey import CreateAccessKey
from euca2ools.commands.iam.getgroup import GetGroup


class CreateUser(IAMRequest):
    DESCRIPTION = 'Create a new user'
    ARGS = [arg_user(help='name of the new user (required)'),
            Arg('-p', '--path', dest='Path',
                help='path for the new user (default: "/")'),
            Arg('-g', '--group-name', route_to=None,
                help='also add the new user to a group'),
            Arg('--verify', action='store_true', route_to=None,
                help='''ensure the group given with -g exists before doing
                anything'''),
            Arg('-k', '--create-accesskey', action='store_true', route_to=None,
                help='also create an access key for the new user and show it'),
            MutuallyExclusiveArgList(
                Arg('-v', '--verbose', action='store_true', route_to=None,
                    help="show the new user's ARN and GUID"),
                Arg('-w', '--write-config', action='store_true', route_to=None,
                    help='''output access keys and region information in the
                    form of a euca2ools.ini(5) configuration file instead of
                    by themselves (implies -k)''')),
            Arg('-d', '--domain', route_to=None, help='''the DNS domain to
                use for region information in configuration file output
                (default: based on IAM URL)'''),
            Arg('-l', '--set-default-user', action='store_true', route_to=None,
                help='''set this user as the default user for the region
                in euca2ools.ini(5) configuration file output.  This
                option is only useful when used with -w.'''),
            AS_ACCOUNT]

    def preprocess(self):
        if self.args.get('verify') and self.args.get('group_name'):
            obj = GetGroup.from_other(
                self, GroupName=self.args['group_name'],
                DelegateAccount=self.params['DelegateAccount'])
            # This will blow up if the group does not exist.
            obj.main()

    def postprocess(self, result):
        if self.args.get('group_name'):
            obj = AddUserToGroup.from_other(
                self, UserName=self.args['UserName'],
                GroupName=self.args['group_name'],
                DelegateAccount=self.params['DelegateAccount'])
            obj.main()
        if self.args.get('create_accesskey') or self.args.get('write_config'):
            obj = CreateAccessKey.from_other(
                self, UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'],
                write_config=self.args.get('write_config'),
                domain=self.args.get('domain'),
                set_default_user=self.args.get('set_default_user'))
            key_result = obj.main()
            result.update(key_result)

    def print_result(self, result):
        if self.args.get('write_config'):
            result['configfile'].write(sys.stdout)
        else:
            if self.args['verbose']:
                print result['User']['Arn']
                print result['User']['UserId']
            if 'AccessKey' in result:
                print result['AccessKey']['AccessKeyId']
                print result['AccessKey']['SecretAccessKey']
