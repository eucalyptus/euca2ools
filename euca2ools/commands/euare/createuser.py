# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2012, Eucalyptus Systems, Inc.
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
from euca2ools.commands.euare.addusertogroup import AddUserToGroup
from euca2ools.commands.euare.createaccesskey import CreateAccessKey
from requestbuilder import Arg


class CreateUser(EuareRequest):
    DESCRIPTION = ('Create a new user and optionally add the user to a group '
                   'or generate an access key for the user')
    ARGS = [Arg('-u', '--user-name', dest='UserName', required=True,
                help='name of the new user'),
            Arg('-p', '--path', dest='Path',
                help='path for the new user (default: "/")'),
            Arg('-g', '--group-name', route_to=None,
                help='add the new user to a group'),
            Arg('-k', '--create-accesskey', action='store_true', route_to=None,
                help='''create an access key for the new user and print it to
                        standard out'''),
            Arg('-v', '--verbose', action='store_true', route_to=None,
                help="print the new user's ARN and GUID"),
            AS_ACCOUNT]

    def postprocess(self, result):
        if self.args.get('group_name'):
            obj = AddUserToGroup(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                GroupName=self.args['group_name'],
                DelegateAccount=self.params['DelegateAccount'])
            obj.main()
        if self.args.get('create_accesskey'):
            obj = CreateAccessKey(
                config=self.config, service=self.service,
                UserName=self.args['UserName'],
                DelegateAccount=self.params['DelegateAccount'])
            key_result = obj.main()
            result.update(key_result)

    def print_result(self, result):
        if self.args['verbose']:
            print result['User']['Arn']
            print result['User']['UserId']
        if 'AccessKey' in result:
            print result['AccessKey']['AccessKeyId']
            print result['AccessKey']['SecretAccessKey']
