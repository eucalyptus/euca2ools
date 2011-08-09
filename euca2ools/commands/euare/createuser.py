# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
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
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

from boto.roboto.awsqueryrequest import AWSQueryRequest
from boto.roboto.param import Param
import euca2ools.commands.euare
import euca2ools.commands.euare.addusertogroup
import euca2ools.commands.euare.createaccesskey


class CreateUser(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """CreateUser"""
    Params = [
        Param(name='Path',
              short_name='p',
              long_name='path',
              ptype='string',
              optional=True,
              doc=""" The path for the User name. For more information about paths, see Identifiers for IAM Entities in Using AWS Identity and Access Management.  This parameter is optional. If it is not included, it defaults to a slash (/). """),
        Param(name='UserName',
              short_name='u',
              long_name='user-name',
              ptype='string',
              optional=False,
              doc=""" Name of the User to create. """),
        Param(name='group_name',
              short_name='g',
              long_name='group-name',
              ptype='string',
              optional=True,
              cardinality='*',
              request_param=False,
              doc="Name of a group you want to add the User to."),
        Param(name='create_accesskey',
              short_name='k',
              long_name='create-accesskey',
              ptype='boolean',
              optional=True,
              default=False,
              request_param=False,
              doc="Creates an access key for the User."),
        Param(name='verbose',
              short_name='v',
              long_name='verbose',
              ptype='boolean',
              optional=True,
              default=False,
              request_param=False,
              doc="causes the response to include the newly created User's ARN and GUID"),
        Param(name='DelegateAccount',
              short_name=None,
              long_name='delegate',
              ptype='string',
              optional=True,
              doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """)]

    Response = {u'type': u'object', u'name': u'CreateUserResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the CreateUser action. '
            ,
        u'type': u'object',
        u'name': u'CreateUserResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' Information about the User. ',
            u'type': u'object',
            u'properties': [{
                u'min_length': 1,
                u'type': u'string',
                u'name': u'Path',
                u'pattern'
                    : u'(\\u002F)|(\\u002F[\\u0021-\\u007F]+\\u002F)',
                u'max_length': 512,
                u'doc'
                    : u' Path to the User name. For more information about paths, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'UserName',
                u'pattern': u'[\\w+=,.@-]*',
                u'max_length': 128,
                u'doc': u' The name identifying the User. ',
                u'optional': False,
                }, {
                u'min_length': 16,
                u'type': u'string',
                u'name': u'UserId',
                u'pattern': u'[\\w]*',
                u'max_length': 32,
                u'doc'
                    : u' The stable and unique string identifying the User. For more information about IDs, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 20,
                u'name': u'Arn',
                u'optional': False,
                u'max_length': 2048,
                u'doc'
                    : u' The Amazon Resource Name (ARN) specifying the User. For more information about ARNs and how to use them in policies, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'type': u'string',
                }],
            u'optional': True,
            u'name': u'User',
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}

    def cli_formatter(self, data):
        if self.cli_options.verbose:
            print data['user_data'].Arn
            print data['user_data'].UserId
        if self.cli_options.create_accesskey:
            print data['access_key'].AccessKey['AccessKeyId']
            print data['access_key'].AccessKey['SecretAccessKey']

    def main(self, **args):
        data = {}
        data['user_data']  = self.send(**args)
        if self.cli_options.group_name:
            obj = euca2ools.commands.euare.addusertogroup.AddUserToGroup()
            for group_name in self.cli_options.group_name:
                data['group_name'] = obj.main(group_name=group_name,
                                              user_name=self.request_params['UserName'])
        if self.cli_options.create_accesskey:
            obj = euca2ools.commands.euare.createaccesskey.CreateAccessKey()
            data['access_key'] = obj.main(user_name=self.request_params['UserName'])
        return data

    def main_cli(self):
        self.do_cli()
