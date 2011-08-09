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


class GetUserInfo(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """GetUserInfo"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=True,
        doc=""" Name of the User. """,
        ), Param(
        name='InfoKey',
        short_name='k',
        long_name='info-key',
        ptype='string',
        optional=True,
        doc=""" Specify the name of the user information to get. """,
        ), Param(
        name='DelegateAccount',
        short_name=None,
        long_name='delegate',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """,
        )]

    Response = {u'type': u'object', u'name': u'GetUserInfoResponse',
                u'properties': [{
        u'doc': u' Contains the result of a successful invocation of the GetUserInfo action. ',
        u'type': u'object',
        u'name': u'GetUserInfoResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' A list of user information name value pairs. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{u'doc': u' The User data type contains information about a User.   This data type is used as a response element in the following actions:  CreateUser GetUser GetUserInfo  ',
                    u'type': u'object', u'properties': [{
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'Key',
                    u'max_length': 512,
                    u'doc': u' User information name. ',
                    u'optional': False,
                    }, {
                    u'min_length': 1,
                    u'name': u'Value',
                    u'optional': False,
                    u'max_length': 2048,
                    u'doc': u' User information value. ',
                    u'type': u'string',
                    }]}],
                }],
            u'optional': False,
            u'name': u'Infos',
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name': u'RequestId'}],
        }]}

    def cli_formatter(self, data):
        for info in data.Infos:
            print info['Key'], "\t", info['Value']


    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
