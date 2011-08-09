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


class ListAccessKeys(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """ListAccessKeys"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=True,
        doc=""" Name of the User. """,
        ), Param(
        name='Marker',
        short_name='m',
        long_name='marker',
        ptype='string',
        optional=True,
        doc=""" Use this only when paginating results, and only in a subsequent request after you've received a response where the results are truncated. Set it to the value of the Marker element in the response you just received. """ ,
        ), Param(
        name='MaxItems',
        short_name=None,
        long_name='max-items',
        ptype='integer',
        optional=True,
        doc=""" Use this only when paginating results to indicate the maximum number of keys you want in the response. If there are additional keys beyond the maximum you specify, the IsTruncated response element is true. """ ,
        ), Param(
        name='DelegateAccount',
        short_name=None,
        long_name='delegate',
        ptype='string',
        optional=True,
        doc=""" [Eucalyptus extension] Use the parameter only as the system admin to act as the account admin of the specified account without changing to account admin's role. """,
        )]

    Response = {u'type': u'object', u'name': u'ListAccessKeysResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the ListAccessKeys action. '
            ,
        u'type': u'object',
        u'name': u'ListAccessKeysResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' A list of access key metadata. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{u'doc'
                           : u' The AccessKey data type contains information about an AWS access key, without its secret key.   This data type is used as a response element in the action ListAccessKeys.  '
                           , u'type': u'object', u'properties': [{
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'UserName',
                    u'pattern': u'[\\w+=,.@-]*',
                    u'max_length': 128,
                    u'doc'
                        : u' Name of the User the key is associated with. '
                        ,
                    u'optional': True,
                    }, {
                    u'min_length': 16,
                    u'type': u'string',
                    u'name': u'AccessKeyId',
                    u'pattern': u'[\\w]*',
                    u'max_length': 32,
                    u'doc': u' The ID for this access key. ',
                    u'optional': True,
                    }, {
                    u'doc'
                        : u' The status of the access key. Active means the key is valid for API calls, while Inactive means it is not. '
                        ,
                    u'type': u'enum',
                    u'name': u'Status',
                    u'optional': True,
                    u'choices': [u'Active', u'Inactive'],
                    }, {
                    u'doc'
                        : u' The date when the access key was created. '
                        ,
                    u'optional': True,
                    u'name': u'CreateDate',
                    u'type': u'dateTime',
                    }]}],
                }],
            u'optional': False,
            u'name': u'AccessKeyMetadata',
            }, {
            u'doc'
                : u' A flag that indicates whether there are more keys to list. If your results were truncated, you can make a subsequent pagination request using the Marker request parameter to retrieve more keys in the list. '
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
                : u' If IsTruncated is true, this element is present and contains the value to use for the Marker parameter in a subsequent pagination request. '
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
        for key in data.AccessKeyMetadata:
            print key['AccessKeyId']
            print key['Status']

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
