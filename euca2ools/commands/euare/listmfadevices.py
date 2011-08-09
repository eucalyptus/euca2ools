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


class ListMFADevices(AWSQueryRequest):

    ServiceClass = euca2ools.commands.euare.Euare

    Description = """ListMFADevices"""
    Params = [Param(
        name='UserName',
        short_name='u',
        long_name='user-name',
        ptype='string',
        optional=False,
        doc=""" Name of the User whose MFA devices you want to list. """
            ,
        ), Param(
        name='Marker',
        short_name='m',
        long_name='marker',
        ptype='string',
        optional=True,
        doc=""" Use this only when paginating results, and only in a subsequent request after you've received a response where the results are truncated. Set it to the value of the Marker element in the response you just received. """
            ,
        ), Param(
        name='MaxItems',
        short_name=None,
        long_name='max-items',
        ptype='integer',
        optional=True,
        doc=""" Use this only when paginating results to indicate the maximum number of keys you want in the response. If there are additional keys beyond the maximum you specify, the IsTruncated response element is true. """
            ,
        )]

    Response = {u'type': u'object', u'name': u'ListMFADevicesResponse',
                u'properties': [{
        u'doc'
            : u' Contains the result of a successful invocation of the ListMFADevices action. '
            ,
        u'type': u'object',
        u'name': u'ListMFADevicesResult',
        u'optional': False,
        u'properties': [{
            u'doc': u' A list of MFA devices. ',
            u'type': u'object',
            u'properties': [{
                u'type': u'array',
                u'optional': False,
                u'name': u'member',
                u'items': [{u'doc'
                           : u' The MFADevice data type contains information about an MFA Device.   This data type is used as a response element in the action ListMFADevices.   '
                           , u'type': u'object', u'properties': [{
                    u'min_length': 1,
                    u'type': u'string',
                    u'name': u'UserName',
                    u'pattern': u'[\\w+=,.@-]*',
                    u'max_length': 128,
                    u'doc'
                        : u' The User with whom the MFA device is associated. '
                        ,
                    u'optional': False,
                    }, {
                    u'min_length': 9,
                    u'type': u'string',
                    u'name': u'SerialNumber',
                    u'pattern': u'[\\w]*',
                    u'max_length': 48,
                    u'doc'
                        : u' Serial number that uniquely identifies the MFA device. '
                        ,
                    u'optional': False,
                    }]}],
                }],
            u'optional': False,
            u'name': u'MFADevices',
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
        for mfa in data.MFADevices:
            print mfa['SerialNumber']

    def main(self, **args):
        return self.send(**args)

    def main_cli(self):
        self.do_cli()
