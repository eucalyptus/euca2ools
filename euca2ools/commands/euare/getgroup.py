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


class GetGroup(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """GetGroup"""
    Params = [Param(
        name='GroupName',
        short_name='g',
        long_name='group-name',
        ptype='string',
        optional=False,
        doc=""" Name of the group. """,
        ), Param(
        name='Marker',
        short_name='m',
        long_name='marker',
        ptype='string',
        optional=True,
        doc=""" Use this only when paginating results, and only in a subsequent request after you've received a response where the results are truncated. Set it to the value of the Marker element in the response you just received. """,
        ), Param(
        name='MaxItems',
        short_name=None,
        long_name='max-items',
        ptype='integer',
        optional=True,
        doc=""" Use this only when paginating results to indicate the maximum number of User names you want in the response. If there are additional User names beyond the maximum you specify, the IsTruncated response element is true. """ ,
        ), Param(
        name='DelegateAccount',
        short_name=None,
        long_name='delegate',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """,
        )]

    Response = {u'type': u'object', u'name': u'GetGroupResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the GetGroup action. '
            ,
        u'type': u'object',
        u'name': u'GetGroupResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' Information about the group. ',
            u'type': u'object',
            u'properties': [{
                u'min_length': 1,
                u'type': u'string',
                u'name': u'Path',
                u'pattern'
                    : u'(\\u002F)|(\\u002F[\\u0021-\\u007F]+\\u002F)',
                u'max_length': 512,
                u'doc'
                    : u' Path to the group. For more information about paths, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 1,
                u'type': u'string',
                u'name': u'GroupName',
                u'pattern': u'[\\w+=,.@-]*',
                u'max_length': 128,
                u'doc': u' The name that identifies the group. ',
                u'optional': False,
                }, {
                u'min_length': 16,
                u'type': u'string',
                u'name': u'GroupId',
                u'pattern': u'[\\w]*',
                u'max_length': 32,
                u'doc'
                    : u' The stable and unique string identifying the group. For more information about IDs, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'optional': False,
                }, {
                u'min_length': 20,
                u'name': u'Arn',
                u'optional': False,
                u'max_length': 2048,
                u'doc'
                    : u' The Amazon Resource Name (ARN) specifying the group. For more information about ARNs and how to use them in policies, see Identifiers for IAM Entities in Using AWS Identity and Access Management. '
                    ,
                u'type': u'string',
                }],
            u'optional': False,
            u'name': u'Group',
            }, {
            u'doc': u' A list of Users in the group. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{u'doc'
                           : u' The User data type contains information about a User.   This data type is used as a response element in the following actions:  CreateUser GetUser ListUsers  '
                           , u'type': u'object', u'properties': [{
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'Path',
                    u'pattern'
                        : u'(\\u002F)|(\\u002F[\\u0021-\\u007F]+\\u002F)'
                        ,
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
                    }]}],
                }],
            u'optional': False,
            u'name': u'Users',
            }, {
            u'doc'
                : u' A flag that indicates whether there are more User names to list. If your results were truncated, you can make a subsequent pagination request using the Marker request parameter to retrieve more User names in the list. '
                ,
            u'optional': True,
            u'name': u'IsTruncated',
            u'type': u'boolean',
            }, {
            u'min_length': 1,
            u'type': u'string',
            u'name': u'Marker',
            u'pattern': u'[\\u0020-\\u00FF]*',
            u'max_length': 320,
            u'doc'
                : u' If IsTruncated is true, then this element is present and contains the value to use for the Marker parameter in a subsequent pagination request. '
                ,
            u'optional': True,
            }],
        }, {
        u'type': u'object',
        u'optional': False,
        u'name': u'ResponseMetadata',
        u'properties': [{u'type': u'string', u'optional': False, u'name'
                        : u'RequestId'}],
        }]}


    def cli_formatter(self, data):
        print data.Group['Arn']
        print '\tusers'
        for user in data.Users:
            print '\t%s' % user['Arn']
            
    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
